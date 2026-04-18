import logging

from dto.automoderation import AutoModerationBatchJobDTO
from services import IAIService

from .notify_auto_moderation_hit import NotifyAutoModerationHitUseCase

logger = logging.getLogger(__name__)


class ProcessAutoModerationBatchUseCase:
    """Вызов модели по готовой пачке и отправка карточки при срабатывании."""

    def __init__(
        self,
        ai_service: IAIService,
        notify_hit_usecase: NotifyAutoModerationHitUseCase,
    ) -> None:
        self._ai = ai_service
        self._notify = notify_hit_usecase

    async def execute(self, dto: AutoModerationBatchJobDTO) -> None:
        if not dto.batch:
            logger.warning(
                "automod batch job: пустая пачка chat_tgid=%s",
                dto.chat_tgid,
            )
            return
        hit = None
        try:
            hit = await self._ai.analyze_spam_batch(dto.chat_title, dto.batch)
        except Exception:
            logger.exception(
                "automod: непойманное исключение LLM chat_tgid=%s",
                dto.chat_tgid,
            )
        if not hit:
            logger.debug(
                "automod: нет срабатывания или ошибка модели chat_tgid=%s",
                dto.chat_tgid,
            )
            return
        if not dto.archive_chat_tgid:
            logger.warning(
                "automod: срабатывание LLM без привязанного архива chat_tgid=%s",
                dto.chat_tgid,
            )
            return
        try:
            await self._notify.execute(
                work_chat_tgid=dto.chat_tgid,
                work_chat_title=dto.chat_title,
                archive_chat_tgid=dto.archive_chat_tgid,
                detection=hit,
            )
        except Exception:
            logger.exception(
                "automod: ошибка отправки карточки в архив chat_tgid=%s",
                dto.chat_tgid,
            )
