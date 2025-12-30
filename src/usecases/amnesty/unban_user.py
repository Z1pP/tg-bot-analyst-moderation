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

            # Собираем информацию об ограничениях до их снятия
            status = await self.user_chat_status_repository.get_status(
                user_id=dto.violator_id,
                chat_id=chat.id,
            )

            is_tg_banned = await self.bot_permission_service.is_member_banned(
                tg_id=dto.violator_tgid,
                chat_tg_id=chat.tg_id,
            )
            is_tg_muted = await self.bot_permission_service.is_member_muted(
                tg_id=dto.violator_tgid,
                chat_tg_id=chat.tg_id,
            )

            # Выполняем и разбан, и размут для полной амнистии
            await self.bot_message_service.unban_chat_member(
                chat_tg_id=chat.tg_id,
                user_tg_id=int(dto.violator_tgid),
            )
            await self.bot_message_service.unmute_chat_member(
                chat_tg_id=chat.tg_id,
                user_tg_id=int(dto.violator_tgid),
            )

            # Всегда обновляем статус в БД и удаляем наказания,
            # так как это "полная амнистия"
            await self.user_chat_status_repository.update_status(
                user_id=dto.violator_id,
                chat_id=chat.id,
                is_banned=False,
                is_muted=False,
                muted_until=None,
            )

            deleted_warns = await self.punishment_service.delete_user_punishments(
                user_id=dto.violator_id,
                chat_id=chat.id,
            )

            # Формируем список того, что было снято
            removed_list = []
            if (status and status.is_banned) or is_tg_banned:
                removed_list.append("бан")
            if (status and status.is_muted) or is_tg_muted:
                removed_list.append("мут")
            if deleted_warns > 0:
                removed_list.append(f"предупреждения ({deleted_warns})")

            removed_text = (
                ", ".join(removed_list) if removed_list else "все ограничения"
            )

            report_text = (
                f"😇 Полная амнистия пользователя @{dto.violator_username}\n\n"
                f"• Снято: <b>{removed_text}</b>\n"
                f"• Администратор: @{dto.admin_username}\n"
                f"• Чат: <b>{chat.title}</b>"
            )

            await self._send_report_to_archives(archive_chats, report_text)
