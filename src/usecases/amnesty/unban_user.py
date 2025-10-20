from dto import AmnestyUserDTO
from repositories import UserChatStatusRepository
from services import (
    BotMessageService,
    BotPermissionService,
    ChatService,
    PunishmentService,
)

from .base_amnesty import BaseAmnestyUseCase


class UnbanUserUseCase(BaseAmnestyUseCase):
    """Разбанивает пользователя и удаляет все его наказания."""

    def __init__(
        self,
        bot_message_service: BotMessageService,
        bot_permission_service: BotPermissionService,
        user_chat_status_repository: UserChatStatusRepository,
        punishment_service: PunishmentService,
        chat_service: ChatService,
    ):
        super().__init__(bot_message_service, bot_permission_service, chat_service)
        self.user_chat_status_repository = user_chat_status_repository
        self.punishment_service = punishment_service

    async def execute(self, dto: AmnestyUserDTO) -> None:
        for chat in dto.chat_dtos:
            archive_chats = await self._validate_and_get_archive_chats(chat)

            success = await self.bot_message_service.unban_chat_member(
                chat_tg_id=chat.tg_id,
                user_tg_id=int(dto.violator_tgid),
            )

            if success:
                await self.user_chat_status_repository.update_status(
                    user_id=dto.violator_id,
                    chat_id=chat.id,
                    is_banned=False,
                    is_muted=False,
                    muted_until=None,
                )

                await self.punishment_service.delete_user_punishments(
                    user_id=dto.violator_id,
                    chat_id=chat.id,
                )

                report_text = (
                    f"😇 Амнистия пользователя @{dto.violator_username}\n\n"
                    f"• Разблокировал: @{dto.admin_username} в чате <b>{chat.title}</b>"
                )

                await self._send_report_to_archives(archive_chats, report_text)
