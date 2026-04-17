"""Тесты ProcessAutoModerationBatchUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from dto.automoderation import (
    AutoModerationBatchJobDTO,
    AutoModerationBufferItemDTO,
    SpamDetectionLLMResultDTO,
)
from usecases.automoderation.process_auto_moderation_batch import (
    ProcessAutoModerationBatchUseCase,
)


def _batch() -> list[AutoModerationBufferItemDTO]:
    return [
        AutoModerationBufferItemDTO(
            username="u",
            user_tg_id=1,
            message_id=10,
            message_text="hello",
        )
    ]


@pytest.mark.asyncio
async def test_execute_no_hit_skips_notify() -> None:
    ai = MagicMock()
    ai.analyze_spam_batch = AsyncMock(return_value=None)
    notify = AsyncMock()
    uc = ProcessAutoModerationBatchUseCase(ai, notify)
    dto = AutoModerationBatchJobDTO(
        chat_tgid="-1001",
        chat_title="G",
        archive_chat_tgid="-1002",
        batch=_batch(),
    )
    await uc.execute(dto)
    ai.analyze_spam_batch.assert_awaited_once()
    notify.execute.assert_not_called()


@pytest.mark.asyncio
async def test_execute_hit_calls_notify() -> None:
    hit = SpamDetectionLLMResultDTO(
        user_tg_id=1,
        message_id=10,
        reason="spam",
        username="u",
    )
    ai = MagicMock()
    ai.analyze_spam_batch = AsyncMock(return_value=hit)
    notify = AsyncMock()
    uc = ProcessAutoModerationBatchUseCase(ai, notify)
    dto = AutoModerationBatchJobDTO(
        chat_tgid="-1001",
        chat_title="G",
        archive_chat_tgid="-1002",
        batch=_batch(),
    )
    await uc.execute(dto)
    notify.execute.assert_awaited_once_with(
        work_chat_tgid="-1001",
        work_chat_title="G",
        archive_chat_tgid="-1002",
        detection=hit,
    )


@pytest.mark.asyncio
async def test_execute_hit_without_archive_skips_notify() -> None:
    hit = SpamDetectionLLMResultDTO(
        user_tg_id=1,
        message_id=10,
        reason="spam",
        username="u",
    )
    ai = MagicMock()
    ai.analyze_spam_batch = AsyncMock(return_value=hit)
    notify = AsyncMock()
    uc = ProcessAutoModerationBatchUseCase(ai, notify)
    dto = AutoModerationBatchJobDTO(
        chat_tgid="-1001",
        chat_title="G",
        archive_chat_tgid=None,
        batch=_batch(),
    )
    await uc.execute(dto)
    notify.execute.assert_not_called()
