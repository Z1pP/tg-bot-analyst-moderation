"""Tests for summary caching behavior."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from config import settings
from constants.enums import SummaryType
from repositories import ChatRepository, MessageRepository, UserTrackingRepository
from services import AdminActionLogService
from services.caching import ICache
from services.chat.summarize import IAIService
from services.chat.summarize.ai_service_base import SummaryResult
from usecases.summarize.summarize_chat_messages import GetChatSummaryUseCase


def _build_usecase():
    msg_repo = AsyncMock(spec=MessageRepository)
    chat_repo = AsyncMock(spec=ChatRepository)
    user_tracking_repo = AsyncMock(spec=UserTrackingRepository)
    ai_service = AsyncMock(spec=IAIService)
    admin_action_log_service = AsyncMock(spec=AdminActionLogService)
    cache = AsyncMock(spec=ICache)

    usecase = GetChatSummaryUseCase(
        msg_repository=msg_repo,
        chat_repository=chat_repo,
        user_tracking_repository=user_tracking_repo,
        ai_service=ai_service,
        admin_action_log_service=admin_action_log_service,
        cache=cache,
    )

    return usecase, msg_repo, chat_repo, user_tracking_repo, ai_service, cache


@pytest.mark.asyncio
async def test_cache_saved_on_success() -> None:
    usecase, msg_repo, chat_repo, user_tracking_repo, ai_service, cache = (
        _build_usecase()
    )

    msg_repo.get_messages_for_summary.return_value = [
        SimpleNamespace(text="Hello world", username="user")
    ]
    msg_repo.get_max_message_id.return_value = 10
    user_tracking_repo.get_tracked_users_by_admin.return_value = []
    chat_repo.get_chat_by_id.return_value = SimpleNamespace(title="Chat")
    cache.get.return_value = None
    ai_service.summarize_text.return_value = SummaryResult(
        status_code=200, summary="summary text"
    )

    result = await usecase.execute(
        chat_id=1,
        summary_type=SummaryType.SHORT,
        admin_tg_id="42",
    )

    assert result == "summary text"
    cache.set.assert_called_once_with(
        key="summary:1:short",
        value=("summary text", 10),
        ttl=settings.SUMMARY_CACHE_TTL_MINUTES * 60,
    )


@pytest.mark.asyncio
async def test_cache_skipped_on_error() -> None:
    usecase, msg_repo, chat_repo, user_tracking_repo, ai_service, cache = (
        _build_usecase()
    )

    msg_repo.get_messages_for_summary.return_value = [
        SimpleNamespace(text="Hello world", username="user")
    ]
    user_tracking_repo.get_tracked_users_by_admin.return_value = []
    chat_repo.get_chat_by_id.return_value = SimpleNamespace(title="Chat")
    cache.get.return_value = None
    ai_service.summarize_text.return_value = SummaryResult(
        status_code=500, summary="error"
    )

    result = await usecase.execute(
        chat_id=1,
        summary_type=SummaryType.SHORT,
        admin_tg_id="42",
    )

    assert result == "error"
    cache.set.assert_not_called()
