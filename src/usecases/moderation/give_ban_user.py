import logging

from constants.punishment import PunishmentText, PunishmentType
from dto import ModerationActionDTO
from repositories.user_chat_status_repository import UserChatStatusRepository
from services import (
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
    ):
        super().__init__(
            user_service,
            bot_message_service,
            chat_service,
            user_chat_status_repository,
            permission_service,
        )
        self.punishment_service = punishment_service

    async def execute(self, dto: ModerationActionDTO) -> None:
        """
        Выполняет бессрочную блокировку пользователя.

        Args:
            dto: Данные о действии модерации

        Raises:
            ModerationError: При ошибках проверок или прав
        """
        context = await self._prepare_moderation_context(dto=dto)

        if not context:
            return

        is_success = await self.bot_message_service.apply_punishmnet(
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
            await self.bot_message_service.delete_message_from_chat(
                chat_id=context.dto.chat_tgid,
                message_id=context.dto.original_message_id,
                message_date=dto.original_message_date,
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

        report_text = self.punishment_service.generate_ban_report(
            dto=context.dto,
            date=correct_date,
            message_deleted=True,
        )

        reason_text = PunishmentText.BAN.value.format(
            username=context.dto.user_reply_username
        )

        admin_answer_text = self.punishment_service.generate_admin_answer(
            archive_chats=context.archive_chats,
            punishment_type=PunishmentType.BAN,
        )

        await self._finalize_moderation(
            context=context,
            report_text=report_text,
            reason_text=reason_text,
            admin_answer_text=admin_answer_text,
        )
