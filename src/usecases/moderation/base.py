from dataclasses import dataclass
from typing import Optional

from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import ChatIdUnion

from constants.enums import UserRole
from dto import ModerationActionDTO
from exceptions.moderation import (
    ArchiveChatError,
    BotInsufficientPermissionsError,
    BotNoAdminRightsInArchiveChatError,
    BotNotInArchiveChatError,
    CannotPunishBotAdminError,
    CannotPunishChatAdminError,
    CannotPunishYouSelf,
    MessageTooOldError,
)
from keyboards.inline.users import hide_notification_ikb
from models import ChatSession, User
from repositories.user_chat_status_repository import UserChatStatusRepository
from services import BotMessageService, BotPermissionService, ChatService, UserService


@dataclass
class ModerationContext:
    dto: ModerationActionDTO
    violator: User
    admin: User
    chat: ChatSession
    archive_chat: Optional[ChatSession] = None
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

    async def _verify_bot_permissions(self, chat: ChatSession) -> None:
        """Проверяет права бота в основном и архивном чатах."""
        # Проверяем что у бота есть необходимые права в основном чате
        bot_can_moderate = await self.permission_service.can_moderate(
            chat_tgid=chat.chat_id,
        )

        if not bot_can_moderate:
            raise BotInsufficientPermissionsError(chat_title=chat.title)

        # Проверка что бот в архивном чате
        is_member = await self.permission_service.is_bot_in_chat(
            chat_tgid=chat.archive_chat_id
        )
        if not is_member:
            raise BotNotInArchiveChatError(
                archive_chat_title=chat.archive_chat.title
                if chat.archive_chat
                else "архивном чате"
            )

        # Проверка прав в архивном чате
        archive_check = await self.permission_service.check_archive_permissions(
            chat_tgid=chat.archive_chat_id
        )
        if not archive_check.is_admin:
            raise BotNoAdminRightsInArchiveChatError(
                archive_chat_title=chat.archive_chat.title
                if chat.archive_chat
                else "архивном чате"
            )

    async def _prepare_moderation_context(
        self, dto: ModerationActionDTO
    ) -> Optional[ModerationContext]:
        if not self.is_different_sender(
            reply_user_tg_id=dto.violator_tgid,
            owner_tg_id=dto.admin_tgid,
        ):
            raise CannotPunishYouSelf()

        chat = await self.chat_service.get_chat_with_archive(
            chat_tgid=dto.chat_tgid,
        )

        if not chat or not chat.archive_chat_id:
            raise ArchiveChatError(chat_title=dto.chat_title)

        await self._verify_bot_permissions(chat)

        if not dto.from_admin_panel and dto.original_message_id:
            await self.bot_message_service.delete_message_from_chat(
                chat_id=dto.chat_tgid,
                message_id=dto.original_message_id,
            )

        violator = await self.user_service.get_or_create(
            tg_id=dto.violator_tgid,
            username=dto.violator_username,
        )
        admin = await self.user_service.get_or_create(
            tg_id=dto.admin_tgid,
            username=dto.admin_username,
        )

        if await self.is_chat_administrator(
            tg_id=dto.violator_tgid,
            chat_tg_id=dto.chat_tgid,
        ):
            raise CannotPunishChatAdminError()

        if self.is_bot_administrator(user=violator):
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
            archive_chat=chat.archive_chat,
        )

    async def _archive_event(
        self, context: ModerationContext, report_text: str
    ) -> None:
        """Отправляет отчет в архивный чат."""
        await self.bot_message_service.send_chat_message(
            chat_tgid=context.archive_chat.chat_id,
            text=report_text,
        )

    async def _cleanup_chat_messages(
        self, context: ModerationContext, report_text: str
    ) -> tuple[bool, str]:
        """Удаляет сообщения из основного чата и обновляет текст отчета если нужно."""
        if context.dto.from_admin_panel:
            return False, report_text

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
                reply_markup=hide_notification_ikb(),
            )

        if not violator_msg_deleted:
            report_text = report_text.replace("удалено", "не удалено (старше 48ч)")

        return violator_msg_deleted, report_text

    async def _notify_participants(
        self,
        context: ModerationContext,
        reason_text: Optional[str],
        admin_answer_text: str,
    ) -> None:
        """Отправляет уведомления в чат и администратору."""
        # Отправляем уведомление в чат только если не из админ-панели
        if reason_text:
            await self.bot_message_service.send_chat_message(
                chat_tgid=context.dto.chat_tgid,
                text=reason_text,
            )

        try:
            if admin_answer_text and not context.dto.from_admin_panel:
                await self.bot_message_service.send_private_message(
                    user_tgid=context.admin.tg_id,
                    text=admin_answer_text,
                )
        except TelegramForbiddenError:
            pass

    async def _finalize_moderation(
        self,
        context: ModerationContext,
        report_text: str,
        reason_text: Optional[str],
        admin_answer_text: str,
    ) -> None:
        if not context.dto.from_admin_panel:
            await self.bot_message_service.forward_message(
                chat_tgid=context.archive_chat.chat_id,
                from_chat_tgid=context.dto.chat_tgid,
                message_tgid=context.dto.reply_message_id,
            )

        violator_msg_deleted, report_text = await self._cleanup_chat_messages(
            context, report_text
        )
        context.message_deleted = violator_msg_deleted

        await self._archive_event(context, report_text)

        await self._notify_participants(context, reason_text, admin_answer_text)
