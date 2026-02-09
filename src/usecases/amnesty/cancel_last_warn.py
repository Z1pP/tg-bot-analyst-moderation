import logging
from dataclasses import asdict

from constants.enums import AdminActionType
from constants.punishment import PunishmentType
from dto import AmnestyUserDTO, CancelWarnResultDTO
from repositories import (
    PunishmentLadderRepository,
    PunishmentRepository,
    UserChatStatusRepository,
)
from services import (
    AdminActionLogService,
    BotMessageService,
    BotPermissionService,
    ChatService,
)
from services.time_service import TimeZoneService

from .base_amnesty import BaseAmnestyUseCase

logger = logging.getLogger(__name__)


class CancelLastWarnUseCase(BaseAmnestyUseCase):
    """Отменяет последнее предупреждение и пересчитывает статус пользователя."""

    def __init__(
        self,
        bot_message_service: BotMessageService,
        bot_permission_service: BotPermissionService,
        punishment_repository: PunishmentRepository,
        punishment_ladder_repository: PunishmentLadderRepository,
        user_chat_status_repository: UserChatStatusRepository,
        chat_service: ChatService,
        admin_action_log_service: AdminActionLogService,
    ):
        super().__init__(bot_message_service, bot_permission_service, chat_service)
        self.punishment_repository = punishment_repository
        self.punishment_ladder_repository = punishment_ladder_repository
        self.user_chat_status_repository = user_chat_status_repository
        self.admin_action_log_service = admin_action_log_service

    async def execute(self, dto: AmnestyUserDTO) -> CancelWarnResultDTO:
        if len(dto.chat_dtos) > 1:
            logger.warning(
                "CancelLastWarnUseCase получил %d чатов, но обработает только первый.",
                len(dto.chat_dtos),
            )
        chat = dto.chat_dtos[0]

        archive_chats = await self._validate_and_get_archive_chats(chat)

        member_status = await self.bot_permission_service.get_chat_member_status(
            chat_tgid=chat.tg_id,
            user_tgid=int(dto.violator_tgid),
        )

        is_deleted = await self.punishment_repository.delete_last_punishment(
            user_id=dto.violator_id, chat_id=chat.id
        )
        if not is_deleted:
            logger.warning("Не найдено наказаний для отмены в чате %s", chat.id)
            return CancelWarnResultDTO(success=False)

        logger.info(
            "Удалено последнее предупреждение для пользователя %s в чате %s",
            dto.violator_username,
            chat.id,
        )

        current_warn_count = await self.punishment_repository.count_punishments(
            user_id=dto.violator_id, chat_id=chat.id
        )

        if current_warn_count == 0 and member_status.is_banned:
            logger.info(
                "Последний варн отменен, снимаем блокировку с пользователя %s",
                dto.violator_username,
            )
            is_unbanned = await self.bot_message_service.unban_chat_member(
                chat_tgid=chat.tg_id, user_tg_id=int(dto.violator_tgid)
            )
            if is_unbanned:
                # Обновляем локальный статус, чтобы отчет был корректным
                member_status.is_banned = False
                member_status.banned_until = None

        # Гарантируем наличие записи в БД перед обновлением
        await self.user_chat_status_repository.get_or_create(
            user_id=dto.violator_id,
            chat_id=chat.id,
        )

        await self.user_chat_status_repository.update_status(
            user_id=dto.violator_id,
            chat_id=chat.id,
            **asdict(member_status),
        )
        logger.info(
            "Статус пользователя %s синхронизирован с Telegram.", dto.violator_username
        )

        next_ladder = await self.punishment_ladder_repository.get_punishment_by_step(
            step=current_warn_count + 1, chat_id=chat.tg_id
        )

        now = TimeZoneService.now()
        date_time_str = now.strftime("%d.%m.%Y %H:%M")
        chat_name = "Все чаты" if len(dto.chat_dtos) > 1 else chat.title

        report_text = (
            "⏮️ Отмена последнего предупреждения\n"
            f"Кто: @{dto.admin_username}\n"
            f"Когда: {date_time_str}\n"
            f"Кого: @{dto.violator_username} ({dto.violator_tgid})\n"
            f"Чат: {chat_name}"
        )

        await self._send_report_to_archives(archive_chats, report_text)

        # Логируем действие администратора
        details = (
            f"Нарушитель: @{dto.violator_username} ({dto.violator_tgid}), "
            f"Чат: {chat.title} ({chat.tg_id})"
        )
        await self.admin_action_log_service.log_action(
            admin_tg_id=dto.admin_tgid,
            action_type=AdminActionType.CANCEL_LAST_WARN,
            details=details,
        )

        return CancelWarnResultDTO(
            success=True,
            current_warns_count=current_warn_count,
            next_punishment_type=next_ladder.punishment_type
            if next_ladder
            else PunishmentType.WARNING,
            next_punishment_duration=(
                next_ladder.duration_seconds if next_ladder else None
            ),
        )
