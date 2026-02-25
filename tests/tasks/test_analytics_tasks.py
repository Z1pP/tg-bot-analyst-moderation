"""Тесты для process_buffered_replies_task."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dto.buffer import BufferedMessageReplyDTO
from repositories.message_reply_repository import MessageReplyRepository
from services.analytics_buffer_service import AnalyticsBufferService
from tasks.analytics_tasks import process_buffered_replies_task


def _make_reply_dto(
    chat_id: int = 1, reply_msg_id: str = "100"
) -> BufferedMessageReplyDTO:
    return BufferedMessageReplyDTO(
        chat_id=chat_id,
        original_message_url="https://t.me/c/1/100",
        reply_message_id_str=reply_msg_id,
        reply_user_id=2,
        response_time_seconds=10,
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_buffer_service() -> MagicMock:
    svc = MagicMock()
    svc.pop_replies = AsyncMock(return_value=[])
    svc.re_add_replies = AsyncMock()
    svc.trim_replies = AsyncMock()
    return svc


@pytest.fixture
def mock_reply_repository() -> MagicMock:
    repo = MagicMock()
    repo.bulk_create_replies = AsyncMock(return_value=(0, []))
    return repo


@pytest.mark.asyncio
async def test_process_buffered_replies_empty_buffer(
    mock_buffer_service: MagicMock,
    mock_reply_repository: MagicMock,
) -> None:
    """При пустом буфере задача не вызывает репозиторий и trim."""
    mock_buffer_service.pop_replies.return_value = []

    def resolve_fn(cls):
        if cls is AnalyticsBufferService:
            return mock_buffer_service
        if cls is MessageReplyRepository:
            return mock_reply_repository
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.analytics_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await process_buffered_replies_task()

    mock_reply_repository.bulk_create_replies.assert_not_called()
    mock_buffer_service.trim_replies.assert_not_called()
    mock_buffer_service.re_add_replies.assert_not_called()


@pytest.mark.asyncio
async def test_process_buffered_replies_all_inserted(
    mock_buffer_service: MagicMock,
    mock_reply_repository: MagicMock,
) -> None:
    """Когда все reply вставлены, trim вызывается, re_add — нет."""
    replies = [_make_reply_dto(), _make_reply_dto(reply_msg_id="101")]
    mock_buffer_service.pop_replies.return_value = replies
    mock_reply_repository.bulk_create_replies.return_value = (2, [])

    def resolve_fn(cls):
        if cls is AnalyticsBufferService:
            return mock_buffer_service
        if cls is MessageReplyRepository:
            return mock_reply_repository
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.analytics_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await process_buffered_replies_task()

    mock_reply_repository.bulk_create_replies.assert_called_once_with(replies)
    mock_buffer_service.re_add_replies.assert_not_called()
    mock_buffer_service.trim_replies.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_process_buffered_replies_none_inserted(
    mock_buffer_service: MagicMock,
    mock_reply_repository: MagicMock,
) -> None:
    """Когда ничего не вставлено, trim и re_add не вызываются."""
    replies = [_make_reply_dto()]
    mock_buffer_service.pop_replies.return_value = replies
    mock_reply_repository.bulk_create_replies.return_value = (0, replies)

    def resolve_fn(cls):
        if cls is AnalyticsBufferService:
            return mock_buffer_service
        if cls is MessageReplyRepository:
            return mock_reply_repository
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.analytics_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await process_buffered_replies_task()

    mock_buffer_service.re_add_replies.assert_not_called()
    mock_buffer_service.trim_replies.assert_not_called()


@pytest.mark.asyncio
async def test_process_buffered_replies_partial_insert(
    mock_buffer_service: MagicMock,
    mock_reply_repository: MagicMock,
) -> None:
    """При частичном успехе failed возвращаются в буфер, затем trim."""
    replies = [
        _make_reply_dto(reply_msg_id="100"),
        _make_reply_dto(reply_msg_id="101"),
        _make_reply_dto(reply_msg_id="102"),
    ]
    failed = [replies[1]]
    mock_buffer_service.pop_replies.return_value = replies
    mock_reply_repository.bulk_create_replies.return_value = (2, failed)

    def resolve_fn(cls):
        if cls is AnalyticsBufferService:
            return mock_buffer_service
        if cls is MessageReplyRepository:
            return mock_reply_repository
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.analytics_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await process_buffered_replies_task()

    mock_buffer_service.re_add_replies.assert_called_once_with(failed)
    mock_buffer_service.trim_replies.assert_called_once_with(3)
