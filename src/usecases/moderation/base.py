from dataclasses import dataclass
from typing import List, Optional

from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import ChatIdUnion

from constants.enums import UserRole
from dto import ModerationActionDTO
from exceptions.moderation import (
    ArchiveChatError,
    BotInsufficientPermissionsError,
    CannotPunishBotAdminError,
    CannotPunishChatAdminError,
    CannotPunishYouSelf,
    MessageTooOldError,
)
from models import ChatSession, User
from repositories.user_chat_status_repository import UserChatStatusRepository
from services import BotMessageService, BotPermissionService, ChatService, UserService


@dataclass
class ModerationContext:
    dto: ModerationActionDTO
    violator: User
    admin: User
    chat: ChatSession
    archive_chats: List[ChatSession]
    message_deleted: bool = True


class ModerationUseCase:
    def __init__(
        self,
        user_service: UserService,
        bot_message_service: BotMessageService,
        chat_service: ChatService,
        user_chat_status_repository: UserChatStatusRepository,
        permission_service: BotPermissionService,
    ):
        self.user_service = user_service
        self.bot_message_service = bot_message_service
        self.chat_service = chat_service
        self.user_chat_status_repository = user_chat_status_repository
        self.permission_service = permission_service

    def is_different_sender(
        self,
        reply_user_tg_id: ChatIdUnion,
        owner_tg_id: ChatIdUnion,
    ) -> bool:
        return reply_user_tg_id != owner_tg_id

    async def is_chat_administrator(
        self,
        tg_id: ChatIdUnion,
        chat_tg_id: ChatIdUnion,
    ) -> bool:
        return await self.permission_service.is_administrator(
            tg_id=tg_id,
            chat_tg_id=chat_tg_id,
        )

    def is_bot_administrator(
        self,
        user: User,
    ) -> bool:
        return user.role == UserRole.ADMIN

    async def _prepare_moderation_context(
        self, dto: ModerationActionDTO
    ) -> Optional[ModerationContext]:
        if not self.is_different_sender(
            reply_user_tg_id=dto.user_reply_tgid,
            owner_tg_id=dto.admin_tgid,
        ):
            raise CannotPunishYouSelf()

        # Проверяем что у бота есть необходимые права чтобы выполнить команду
        bot_can_moderate = await self.permission_service.can_moderate(
            chat_tgid=dto.chat_tgid,
        )

        if not bot_can_moderate:
            raise BotInsufficientPermissionsError(chat_title=dto.chat_title)

        if await self.is_chat_administrator(
            tg_id=dto.user_reply_tgid,
            chat_tg_id=dto.chat_tgid,
        ):
            await self.bot_message_service.delete_message_from_chat(
                chat_id=dto.chat_tgid,
                message_id=dto.original_message_id,
            )
            raise CannotPunishChatAdminError()

        archive_chats = await self.chat_service.get_archive_chats(
            source_chat_title=dto.chat_title,
        )

        if not archive_chats:
            await self.bot_message_service.delete_message_from_chat(
                chat_id=dto.chat_tgid,
                message_id=dto.original_message_id,
            )
            raise ArchiveChatError()

        violator = await self.user_service.get_user(
            tg_id=dto.user_reply_tgid,
            username=dto.user_reply_username,
        )
        admin = await self.user_service.get_user(
            tg_id=dto.admin_tgid,
            username=dto.admin_username,
        )
        chat = await self.chat_service.get_chat(
            chat_id=dto.chat_tgid,
            title=dto.chat_title,
        )

        if self.is_bot_administrator(user=violator):
            await self.bot_message_service.delete_message_from_chat(
                chat_id=dto.chat_tgid,
                message_id=dto.original_message_id,
            )
            raise CannotPunishBotAdminError()

        await self.user_chat_status_repository.get_or_create(
            user_id=violator.id,
            chat_id=chat.id,
        )

        return ModerationContext(
            dto=dto,
            violator=violator,
            admin=admin,
            chat=chat,
            archive_chats=archive_chats,
        )

    async def _finalize_moderation(
        self,
        context: ModerationContext,
        report_text: str,
        reason_text: str,
        admin_answer_text: str,
    ) -> None:
        for archive_chat in context.archive_chats:
            await self.bot_message_service.forward_message(
                chat_tgid=archive_chat.chat_id,
                from_chat_tgid=context.dto.chat_tgid,
                message_tgid=context.dto.reply_message_id,
            )

        try:
            violator_msg_deleted = (
                await self.bot_message_service.delete_message_from_chat(
                    chat_id=context.dto.chat_tgid,
                    message_id=context.dto.reply_message_id,
                    message_date=context.dto.reply_message_date,
                )
            )
        except MessageTooOldError as e:
            violator_msg_deleted = False
            await self.bot_message_service.send_private_message(
                user_tgid=context.admin.tg_id,
                text=e.get_user_message(),
            )

        if not violator_msg_deleted:
            report_text = report_text.replace("удалено", "не удалено (старше 48ч)")

        for archive_chat in context.archive_chats:
            await self.bot_message_service.send_chat_message(
                chat_tgid=archive_chat.chat_id,
                text=report_text,
            )

        await self.bot_message_service.delete_message_from_chat(
            chat_id=context.dto.chat_tgid,
            message_id=context.dto.original_message_id,
            message_date=context.dto.original_message_date,
        )

        await self.bot_message_service.send_chat_message(
            chat_tgid=context.dto.chat_tgid,
            text=reason_text,
        )

        try:
            await self.bot_message_service.send_private_message(
                user_tgid=context.admin.tg_id,
                text=admin_answer_text,
            )
        except TelegramForbiddenError:
            pass

        context.message_deleted = violator_msg_deleted

    async def _send_messages_to_admins(
        self,
        dto: ModerationActionDTO,
        text: str,
    ) -> None:
        admins = await self.user_service.get_admins_for_chat(chat_tg_id=dto.chat_tgid)

        if not admins:
            return

        extended_text = (
            f"Администратор @{dto.admin_username} попытался выдать "
            f"предупреждение пользователю @{dto.user_reply_username} в чате {dto.chat_title},"
            "однако отсутсвует чат с историей удалённых сообщений.\n\n" + text
        )

        admins = [admin for admin in admins if admin.tg_id != dto.admin_tgid]

        for admin in admins:
            try:
                await self.bot_message_service.send_private_message(
                    user_tgid=admin.tg_id,
                    text=extended_text,
                )
            except TelegramForbiddenError:
                pass
