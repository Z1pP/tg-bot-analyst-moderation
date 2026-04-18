"""Тесты постановки пачки автомодерации в очередь."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dto.automoderation import AutoModerationBufferItemDTO, AutoModerationRunDTO
from services.automoderation_buffer_service import AutoModerationBufferService
from usecases.automoderation.run_auto_moderation_on_message import (
    RunAutoModerationOnMessageUseCase,
)


@pytest.mark.asyncio
async def test_full_batch_enqueues_task() -> None:
    batch = [
        AutoModerationBufferItemDTO(
            username="a",
            user_tg_id=1,
            message_id=1,
            message_text="x",
        )
    ]
    buffer = MagicMock(spec=AutoModerationBufferService)
    buffer.append_text_message = AsyncMock(return_value=batch)

    mock_task = MagicMock()
    mock_task.kiq = AsyncMock()

    dto = AutoModerationRunDTO(
        chat_tgid="-100",
        chat_title="Chat",
        is_auto_moderation_enabled=True,
        archive_chat_tgid="-200",
        username="u",
        user_tg_id=99,
        message_id=5,
        message_text="hello",
    )

    uc = RunAutoModerationOnMessageUseCase(buffer, batch_size=30)
    with patch(
        "tasks.automoderation_tasks.process_auto_moderation_batch_task",
        mock_task,
    ):
        await uc.execute(dto)

    buffer.append_text_message.assert_awaited_once()
    mock_task.kiq.assert_awaited_once()
    call_kw = mock_task.kiq.await_args.kwargs
    assert call_kw["chat_tgid"] == "-100"
    assert call_kw["chat_title"] == "Chat"
    assert call_kw["archive_chat_tgid"] == "-200"
    assert len(call_kw["batch_items"]) == 1
    assert call_kw["batch_items"][0]["user_tg_id"] == 1


@pytest.mark.asyncio
async def test_partial_batch_no_enqueue() -> None:
    buffer = MagicMock(spec=AutoModerationBufferService)
    buffer.append_text_message = AsyncMock(return_value=None)

    mock_task = MagicMock()
    mock_task.kiq = AsyncMock()

    dto = AutoModerationRunDTO(
        chat_tgid="-100",
        chat_title="Chat",
        is_auto_moderation_enabled=True,
        archive_chat_tgid="-200",
        username="u",
        user_tg_id=99,
        message_id=5,
        message_text="hello",
    )

    uc = RunAutoModerationOnMessageUseCase(buffer, batch_size=30)
    with patch(
        "tasks.automoderation_tasks.process_auto_moderation_batch_task",
        mock_task,
    ):
        await uc.execute(dto)

    mock_task.kiq.assert_not_called()
