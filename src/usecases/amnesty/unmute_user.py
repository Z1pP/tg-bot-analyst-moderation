from constants.enums import AdminActionType
from dto import AmnestyUserDTO
from repositories import UserChatStatusRepository
from services import (
    AdminActionLogService,
    BotMessageService,
    BotPermissionService,
    ChatService,
)
from services.time_service import TimeZoneService
from utils.moderation import format_violator_display

from .base_amnesty import BaseAmnestyUseCase


class UnmuteUserUseCase(BaseAmnestyUseCase):
    """Размучивает пользователя в чате."""

    def __init__(
        self,
        bot_message_service: BotMessageService,
        bot_permission_service: BotPermissionService,
        user_chat_status_repository: UserChatStatusRepository,
        chat_service: ChatService,
        admin_action_log_service: AdminActionLogService,
    ):
        super().__init__(bot_message_service, bot_permission_service, chat_service)
        self.user_chat_status_repository = user_chat_status_repository
        self.admin_action_log_service = admin_action_log_service

    async def execute(self, dto: AmnestyUserDTO) -> None:
        for chat in dto.chat_dtos:
            archive_chats = await self._validate_and_get_archive_chats(chat)

            # Проверяем текущий статус в Telegram API
            member_status = await self.bot_permission_service.get_chat_member_status(
                user_id=int(dto.violator_tgid),
                chat_tgid=chat.tg_id,
            )

            # Размучиваем в Telegram только если пользователь действительно замучен
            if member_status.is_muted:
                await self.bot_message_service.unmute_chat_member(
                    chat_tg_id=chat.tg_id,
                    user_tg_id=int(dto.violator_tgid),
                )

            # Синхронизируем статус в БД
            await self.user_chat_status_repository.get_or_create(
                user_id=dto.violator_id,
                chat_id=chat.id,
                defaults={
                    "is_muted": False,
                    "muted_until": None,
                },
            )

            await self.user_chat_status_repository.update_status(
                user_id=dto.violator_id,
                chat_id=chat.id,
                is_muted=False,
                muted_until=None,
            )

            now = TimeZoneService.now()
            date_time_str = now.strftime("%d.%m.%Y %H:%M")
            chat_name = "Все чаты" if len(dto.chat_dtos) > 1 else chat.title
            violator_display = format_violator_display(
                dto.violator_username, dto.violator_tgid
            )

            admin_display = format_violator_display(dto.admin_username, dto.admin_tgid)
            report_text = (
                "🔊 Размут\n"
                f"Кто: {admin_display}\n"
                f"Когда: {date_time_str}\n"
                f"Кого: {violator_display} ({dto.violator_tgid})\n"
                f"Чат: {chat_name}"
            )

            await self._send_report_to_archives(archive_chats, report_text)

            # Логируем действие администратора
            details = (
                f"Нарушитель: {violator_display} ({dto.violator_tgid}), "
                f"Чат: {chat.title} ({chat.tg_id})"
            )
            await self.admin_action_log_service.log_action(
                admin_tg_id=dto.admin_tgid,
                action_type=AdminActionType.UNMUTE_USER,
                details=details,
            )
