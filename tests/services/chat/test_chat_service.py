"""Тесты ChatService: get_chat_with_archive, get_or_create."""

from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest

from models import ChatSession
from repositories import ChatRepository
from services.caching import ICache
from services.chat.chat_service import ChatService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=ChatRepository)


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock(spec=ICache)


@pytest.fixture
def chat_service(mock_repo: AsyncMock, mock_cache: AsyncMock) -> ChatService:
    return ChatService(chat_repository=mock_repo, cache=mock_cache)


@pytest.fixture
def sample_chat() -> MagicMock:
    """Чат с настройками времени для форматирования в хендлерах."""
    chat = MagicMock(spec=ChatSession)
    chat.id = 1
    chat.chat_id = "-100"
    chat.title = "Test Chat"
    chat.start_time = time(9, 0)
    chat.end_time = time(18, 0)
    chat.archive_chat_id = None
    return chat


@pytest.mark.asyncio
async def test_get_chat_with_archive_value_error_when_no_args(
    chat_service: ChatService,
) -> None:
    """get_chat_with_archive без chat_tgid и chat_id поднимает ValueError."""
    with pytest.raises(ValueError, match="chat_tgid или chat_id"):
        await chat_service.get_chat_with_archive(chat_tgid=None, chat_id=None)


@pytest.mark.asyncio
async def test_get_chat_with_archive_by_chat_id_returns_chat(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """get_chat_with_archive(chat_id=...) возвращает чат из репозитория."""
    mock_repo.get_chat_by_id = AsyncMock(return_value=sample_chat)

    result = await chat_service.get_chat_with_archive(chat_id=1)

    assert result is sample_chat
    mock_repo.get_chat_by_id.assert_called_once_with(chat_id=1)


@pytest.mark.asyncio
async def test_get_chat_with_archive_by_tgid_returns_chat(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """get_chat_with_archive(chat_tgid=...) возвращает чат из репозитория."""
    mock_repo.get_chat_by_tgid = AsyncMock(return_value=sample_chat)

    result = await chat_service.get_chat_with_archive(chat_tgid="-100")

    assert result is sample_chat
    mock_repo.get_chat_by_tgid.assert_called_once_with("-100")


@pytest.mark.asyncio
async def test_get_or_create_returns_existing(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """get_or_create при найденном чате возвращает его."""
    mock_cache.get = AsyncMock(return_value=None)
    mock_repo.get_chat_by_tgid = AsyncMock(return_value=sample_chat)

    result = await chat_service.get_or_create(chat_tgid="-100", title=None)

    assert result is sample_chat
    mock_repo.create_chat.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_creates_when_not_found(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """get_or_create при отсутствии чата создаёт новый и возвращает его."""
    mock_cache.get = AsyncMock(return_value=None)
    mock_repo.get_chat_by_tgid = AsyncMock(return_value=None)
    mock_repo.create_chat = AsyncMock(return_value=sample_chat)

    result = await chat_service.get_or_create(chat_tgid="-100", title="New")

    assert result is sample_chat
    mock_repo.create_chat.assert_called_once_with(chat_id="-100", title="New")
    mock_cache.set.assert_called()
