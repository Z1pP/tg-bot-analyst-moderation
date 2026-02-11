import logging

from constants.enums import AdminActionType
from constants.punishment import PunishmentType
from dto import ModerationActionDTO
from exceptions.moderation import ModerationError
from repositories.user_chat_status_repository import UserChatStatusRepository
from services import (
    AdminActionLogService,
    BotMessageService,
    BotPermissionService,
    ChatService,
    PunishmentService,
    UserService,
)
from services.time_service import TimeZoneService

from .base import ModerationUseCase

logger = logging.getLogger(__name__)


class GiveUserBanUseCase(ModerationUseCase):
    """
    Use case для бессрочной блокировки пользователя в чате.

    Алгоритм работы:
    1. Подготовка контекста (проверки, получение данных)
    2. Применение бана в Telegram
    3. Обновление статуса в БД
    4. Генерация отчета
    5. Финализация (пересылка в архив, удаление, уведомление)
    """

    def __init__(
        self,
        user_service: UserService,
        bot_message_service: BotMessageService,
        chat_service: ChatService,
        punishment_service: PunishmentService,
        user_chat_status_repository: UserChatStatusRepository,
        permission_service: BotPermissionService,
        admin_action_log_service: AdminActionLogService,
    ):
        super().__init__(
            user_service,
            bot_message_service,
            chat_service,
            user_chat_status_repository,
            permission_service,
        )
        self.punishment_service = punishment_service
        self.admin_action_log_service = admin_action_log_service

    async def execute(self, dto: ModerationActionDTO) -> None:
        """
        Выполняет бессрочную блокировку пользователя.

        Args:
            dto: Данные о действии модерации

        Raises:
            ModerationError: При ошибках проверок или прав
        """
        try:
            context = await self._prepare_moderation_context(dto=dto)
        except ModerationError as e:
            await self.bot_message_service.send_private_message(
                user_tgid=dto.admin_tgid,
                text=e.get_user_message(),
            )
            return

        if not context:
            return

        is_success = await self.bot_message_service.apply_punishment(
            chat_tg_id=context.chat.chat_id,
            user_tg_id=context.violator.tg_id,
            action=PunishmentType.BAN,
        )

        if not is_success:
            logger.error(
                "Не удалось забанить пользователя %s в чате %s",
                context.violator.tg_id,
                context.chat.chat_id,
            )
            return

        try:
            await self.user_chat_status_repository.update_status(
                user_id=context.violator.id,
                chat_id=context.chat.id,
                is_banned=True,
            )
        except Exception as e:
            logger.error(
                "Ошибка при обновлении статуса для пользователя %s: %s",
                context.violator.id,
                e,
                exc_info=True,
            )
            return

        correct_date = TimeZoneService.now()

        violator_display = self._get_violator_display_name(
            username=context.dto.violator_username,
            tg_id=context.violator.tg_id,
        )

        report_text = self.punishment_service.generate_ban_report(
            dto=context.dto,
            date=correct_date,
            message_deleted=True,
        )

        reason_text = self.punishment_service.generate_reason_for_user(
            duration_of_punishment=0,
            violator_username=context.dto.violator_username,
            violator_tg_id=context.violator.tg_id,
            punishment_type=PunishmentType.BAN,
        )

        await self._finalize_moderation(
            context=context,
            report_text=report_text,
            reason_text=reason_text,
            admin_answer_text="",
        )

        # Логируем действие администратора
        details = (
            f"Нарушитель: {violator_display} ({context.violator.tg_id}), "
            f"Чат: {context.chat.title} ({context.chat.chat_id}), "
            f"Период: бессрочно"
        )
        await self.admin_action_log_service.log_action(
            admin_tg_id=dto.admin_tgid,
            action_type=AdminActionType.BAN_USER,
            details=details,
        )

    @staticmethod
    def _get_violator_display_name(username: str | None, tg_id: str) -> str:
        if username and username != "hidden":
            return f"@{username}"
        return f"ID:{tg_id}"
