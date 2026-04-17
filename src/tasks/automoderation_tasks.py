"""Фоновые задачи автомодерации (очередь RabbitMQ / TaskIQ)."""

from __future__ import annotations

import logging
from typing import Any

from container import ContainerSetup, container
from dto.automoderation import AutoModerationBatchJobDTO, AutoModerationBufferItemDTO
from scheduler import broker
from usecases.automoderation.process_auto_moderation_batch import (
    ProcessAutoModerationBatchUseCase,
)

logger = logging.getLogger(__name__)

ContainerSetup.setup()


@broker.task
async def process_auto_moderation_batch_task(
    chat_tgid: str,
    chat_title: str,
    archive_chat_tgid: str | None,
    batch_items: list[dict[str, Any]],
) -> None:
    """
    Обрабатывает пачку из N текстовых сообщений: LLM и при необходимости карточка в архив.

    Аргументы сериализуемы для брокера; список сообщений — dict из AutoModerationBufferItemDTO.
    """
    try:
        batch = [AutoModerationBufferItemDTO.model_validate(x) for x in batch_items]
    except Exception:
        logger.exception(
            "automod task: не удалось разобрать пачку chat_tgid=%s len=%s",
            chat_tgid,
            len(batch_items),
        )
        return

    dto = AutoModerationBatchJobDTO(
        chat_tgid=chat_tgid,
        chat_title=chat_title,
        archive_chat_tgid=archive_chat_tgid,
        batch=batch,
    )
    try:
        uc: ProcessAutoModerationBatchUseCase = container.resolve(
            ProcessAutoModerationBatchUseCase
        )
        await uc.execute(dto)
    except Exception:
        logger.exception(
            "automod task: ошибка выполнения use case chat_tgid=%s",
            chat_tgid,
        )
