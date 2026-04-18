import logging

from dto.automoderation import AutoModerationBufferItemDTO, AutoModerationRunDTO
from services.automoderation_buffer_service import AutoModerationBufferService

logger = logging.getLogger(__name__)


class RunAutoModerationOnMessageUseCase:
    """Буфер Redis; при заполнении пачки — постановка задачи в очередь (LLM в воркере)."""

    def __init__(
        self,
        buffer_service: AutoModerationBufferService,
        batch_size: int,
    ) -> None:
        self._buffer = buffer_service
        self._batch_size = batch_size

    async def execute(self, dto: AutoModerationRunDTO) -> None:
        if not dto.is_auto_moderation_enabled:
            return
        text = (dto.message_text or "").strip()
        if not text:
            return
        item = AutoModerationBufferItemDTO(
            username=dto.username,
            user_tg_id=dto.user_tg_id,
            message_id=dto.message_id,
            message_text=text[:4096],
        )
        try:
            batch = await self._buffer.append_text_message(
                dto.chat_tgid,
                item,
                self._batch_size,
            )
        except Exception:
            logger.exception(
                "automod: ошибка буфера Redis chat_tgid=%s",
                dto.chat_tgid,
            )
            return
        if batch is None:
            return
        if not batch:
            logger.warning(
                "automod: пачка пуста после flush (десериализация?) chat_tgid=%s",
                dto.chat_tgid,
            )
            return

        try:
            from tasks.automoderation_tasks import process_auto_moderation_batch_task

            batch_items = [m.model_dump(mode="json") for m in batch]
            await process_auto_moderation_batch_task.kiq(
                chat_tgid=dto.chat_tgid,
                chat_title=dto.chat_title,
                archive_chat_tgid=dto.archive_chat_tgid,
                batch_items=batch_items,
            )
        except Exception:
            logger.exception(
                "automod: не удалось поставить задачу в очередь "
                "(пачка уже сброшена из Redis) chat_tgid=%s batch_size=%s",
                dto.chat_tgid,
                len(batch),
            )
