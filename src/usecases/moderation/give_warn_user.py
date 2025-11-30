import logging

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


class GiveUserWarnUseCase(ModerationUseCase):
    """
    Use case для выдачи предупреждения пользователю с применением PunishmentLadder.

    Алгоритм работы:
    1. Подготовка контекста (проверки, получение данных)
    2. Получение текущего количества наказаний пользователя
    3. Определение наказания по PunishmentLadder
    4. Применение наказания в Telegram (mute/ban/warning)
    5. Сохранение в БД (наказание + статус)
    6. Генерация отчета
    7. Финализация (пересылка в архив, удаление, уведомление)

    Особенности:
    - Автоматически применяет максимальное наказание при превышении лимита
    - Транзакционно сохраняет наказание и статус
    - Обрабатывает старые сообщения (>48ч)
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
        Выполняет выдачу предупреждения с применением соответствующего наказания.

        Args:
            dto: Данные о действии модерации

        Raises:
            ModerationError: При ошибках проверок или прав
        """
        context = await self._prepare_moderation_context(dto=dto)

        if not context:
            return

        # Получаем номер следующего наканазания и само наказание из БД
        punishment_count = await self.punishment_service.get_punishment_count(
            user_id=context.violator.id,
        )
        punishment_ladder = await self.punishment_service.get_punishment(
            warn_count=punishment_count,
            chat_id=context.dto.chat_tgid,
        )

        # Применяем наказание в чате для нарушителя
        is_success = await self.bot_message_service.apply_punishmnet(
            chat_tg_id=context.chat.chat_id,
            user_tg_id=context.violator.tg_id,
            action=punishment_ladder.punishment_type,
            duration_seconds=punishment_ladder.duration_seconds,
        )

        if not is_success:
            logger.error(
                "Не удалось применить наказание для пользователя %s в чате %s",
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
            await self.punishment_service.save_punishment_with_status(
                user=context.violator,
                punishment=punishment_ladder,
                admin_id=context.admin.id,
                chat_id=context.chat.id,
            )
        except Exception as e:
            logger.error(
                "Ошибка при сохранении наказания для пользователя %s: %s",
                context.violator.id,
                e,
                exc_info=True,
            )
            return

        current_date = TimeZoneService.now()

        reason_text = self.punishment_service.generate_reason_for_user(
            punishment_type=punishment_ladder.punishment_type,
            duration_of_punishment=punishment_ladder.duration_seconds,
            punished_username=context.violator.username,
        )

        report = self.punishment_service.generate_report(
            dto=context.dto,
            punishment_ladder=punishment_ladder,
            date=current_date,
            message_deleted=True,
        )

        admin_answer_text = self.punishment_service.generate_admin_answer(
            archive_chats=context.archive_chat,
            punishment_type=punishment_ladder.punishment_type,
        )

        await self._finalize_moderation(
            context=context,
            report_text=report,
            reason_text=reason_text,
            admin_answer_text=admin_answer_text,
        )
