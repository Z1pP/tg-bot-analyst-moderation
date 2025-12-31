from constants.enums import AdminActionType
from dto import AmnestyUserDTO
from repositories import UserChatStatusRepository
from services import (
    AdminActionLogService,
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
        admin_action_log_service: AdminActionLogService,
    ):
        super().__init__(bot_message_service, bot_permission_service, chat_service)
        self.user_chat_status_repository = user_chat_status_repository
        self.punishment_service = punishment_service
        self.admin_action_log_service = admin_action_log_service

    async def execute(self, dto: AmnestyUserDTO) -> None:
        for chat in dto.chat_dtos:
            archive_chats = await self._validate_and_get_archive_chats(chat)

            # Собираем информацию об ограничениях до их снятия из Telegram API
            member_status = await self.bot_permission_service.get_chat_member_status(
                user_tgid=int(dto.violator_tgid),
                chat_tgid=chat.tg_id,
            )

            # Выполняем разбан и размут в Telegram, если это необходимо
            if member_status.is_banned:
                await self.bot_message_service.unban_chat_member(
                    chat_tg_id=chat.tg_id,
                    user_tg_id=int(dto.violator_tgid),
                )

            if member_status.is_muted:
                await self.bot_message_service.unmute_chat_member(
                    chat_tg_id=chat.tg_id,
                    user_tg_id=int(dto.violator_tgid),
                )

            # Гарантируем наличие записи в БД и её актуальность (синхронизация)
            await self.user_chat_status_repository.get_or_create(
                user_id=dto.violator_id,
                chat_id=chat.id,
                defaults={
                    "is_banned": False,
                    "is_muted": False,
                    "muted_until": None,
                },
            )

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

            removed_list = []
            if member_status.is_banned:
                removed_list.append("бан")
            if member_status.is_muted:
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

            # Логируем действие администратора
            details = (
                f"Нарушитель: @{dto.violator_username} ({dto.violator_tgid}), "
                f"Чат: {chat.title} ({chat.tg_id})"
            )
            await self.admin_action_log_service.log_action(
                admin_tg_id=dto.admin_tgid,
                action_type=AdminActionType.UNBAN_USER,
                details=details,
            )
