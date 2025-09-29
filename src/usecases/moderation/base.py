from dataclasses import dataclass
from typing import List, Optional

from dto import ModerationActionDTO
from models import ChatSession, User
from repositories.user_chat_status_repository import UserChatStatusRepository
from services import BotMessageService, ChatService, UserService


@dataclass
class ModerationContext:
    dto: ModerationActionDTO
    violator: User
    admin: User
    chat: ChatSession
    archive_chats: List[ChatSession]


class ModerationUseCase:
    def __init__(
        self,
        user_service: UserService,
        bot_message_service: BotMessageService,
        chat_service: ChatService,
        user_chat_status_repository: UserChatStatusRepository,
    ):
        self.user_service = user_service
        self.bot_message_service = bot_message_service
        self.chat_service = chat_service
        self.user_chat_status_repository = user_chat_status_repository

    def is_different_sender(self, dto: ModerationActionDTO) -> bool:
        return dto.user_reply_tgid != dto.admin_tgid

    async def _prepare_moderation_context(
        self, dto: ModerationActionDTO
    ) -> Optional[ModerationContext]:
        if not self.is_different_sender(dto=dto):
            return None

        archive_chats = await self.chat_service.get_archive_chats(
            source_chat_title=dto.chat_title,
        )
        if not archive_chats:
            text = (
                "Пожалуйста, создайте рабочий чат с историей удалённых сообщений и"
                " добавьте его в Аналиста. В будущем это облегчит работу при поиске "
                "заблокированных пользователей."
            )
            await self.bot_message_service.send_private_message(
                user_tgid=dto.admin_tgid,
                text=text,
            )
            await self._send_messages_to_admins(dto=dto, text=text)
            return None

        violator = await self.user_service.get_user(tg_id=dto.user_reply_tgid)
        admin = await self.user_service.get_user(tg_id=dto.admin_tgid)
        chat = await self.chat_service.get_chat(title=dto.chat_title)

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
    ) -> None:
        for archive_chat in context.archive_chats:
            await self.bot_message_service.forward_message(
                chat_tgid=archive_chat.chat_id,
                from_chat_tgid=context.dto.chat_tgid,
                message_tgid=context.dto.reply_message_id,
            )

            await self.bot_message_service.send_chat_message(
                chat_tgid=archive_chat.chat_id,
                text=report_text,
            )

        await self.bot_message_service.delete_message_from_chat(
            chat_id=context.dto.chat_tgid, message_id=context.dto.reply_message_id
        )

        await self.bot_message_service.send_chat_message(
            chat_tgid=context.dto.chat_tgid, text=reason_text
        )

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
            await self.bot_message_service.send_private_message(
                user_tgid=admin.tg_id,
                text=extended_text,
            )
