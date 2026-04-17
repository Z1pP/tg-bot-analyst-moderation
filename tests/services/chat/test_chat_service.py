"""Тесты ChatService: get_chat, get_or_create, update_chat_title, get_chat_with_archive."""

from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from dto.chat_dto import ChatSessionCacheDTO
from exceptions import DatabaseException
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


@pytest.mark.asyncio
async def test_get_chat_from_cache_returns_cached(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """get_chat материализует ChatSession из ChatSessionCacheDTO в Redis."""
    cached = ChatSessionCacheDTO(
        id=1,
        chat_id="-100",
        title="Test Chat",
        archive_chat_id=None,
        is_auto_moderation_enabled=True,
    )
    mock_cache.get = AsyncMock(return_value=cached)

    result = await chat_service.get_chat(chat_tgid="-100")

    assert result is not None
    assert result.id == 1
    assert result.chat_id == "-100"
    assert result.title == "Test Chat"
    assert result.is_auto_moderation_enabled is True
    mock_cache.get.assert_called_once_with("chat:tg_id:-100")
    mock_repo.get_chat_by_tgid.assert_not_called()


@pytest.mark.asyncio
async def test_get_chat_from_repo_when_not_in_cache(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """get_chat загружает из репозитория и кеширует при отсутствии в кеше."""
    mock_cache.get = AsyncMock(return_value=None)
    mock_repo.get_chat_by_tgid = AsyncMock(return_value=sample_chat)

    result = await chat_service.get_chat(chat_tgid="-100")

    assert result is sample_chat
    mock_repo.get_chat_by_tgid.assert_called_once_with("-100")
    mock_cache.set.assert_called()


@pytest.mark.asyncio
async def test_get_chat_updates_title_when_different_from_cache(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """get_chat обновляет title в БД и кеше при расхождении (чат из кеша)."""
    cached = ChatSessionCacheDTO(
        id=1,
        chat_id="-100",
        title="Old Title",
        archive_chat_id=None,
    )
    updated_chat = MagicMock(spec=ChatSession)
    updated_chat.id = 1
    updated_chat.chat_id = "-100"
    updated_chat.title = "New Title"
    updated_chat.archive_chat_id = None
    mock_cache.get = AsyncMock(return_value=cached)
    mock_repo.update_chat = AsyncMock(return_value=updated_chat)

    result = await chat_service.get_chat(chat_tgid="-100", title="New Title")

    assert result.title == "New Title"
    mock_repo.update_chat.assert_called_once_with(chat_id=1, title="New Title")
    mock_cache.set.assert_called()


@pytest.mark.asyncio
async def test_get_chat_returns_none_when_not_found(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """get_chat возвращает None при отсутствии чата."""
    mock_cache.get = AsyncMock(return_value=None)
    mock_repo.get_chat_by_tgid = AsyncMock(return_value=None)

    result = await chat_service.get_chat(chat_tgid="-100")

    assert result is None


@pytest.mark.asyncio
async def test_update_chat_title_success(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """update_chat_title обновляет title и синхронизирует кеш."""
    sample_chat.title = "Updated Title"
    mock_repo.update_chat = AsyncMock(return_value=sample_chat)

    result = await chat_service.update_chat_title(chat_id=1, title="Updated Title")

    assert result is sample_chat
    mock_repo.update_chat.assert_called_once_with(chat_id=1, title="Updated Title")
    mock_cache.set.assert_called()


@pytest.mark.asyncio
async def test_update_chat_title_returns_none_when_repo_returns_none(
    chat_service: ChatService,
    mock_repo: AsyncMock,
) -> None:
    """update_chat_title возвращает None если репозиторий не нашёл чат."""
    mock_repo.update_chat = AsyncMock(return_value=None)

    result = await chat_service.update_chat_title(chat_id=999, title="Title")

    assert result is None


@pytest.mark.asyncio
async def test_get_chat_with_archive_from_in_memory_cache(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """get_chat_with_archive возвращает чат из in-memory кеша при chat_tgid."""
    mock_repo.get_chat_by_tgid = AsyncMock(return_value=sample_chat)
    await chat_service.get_chat_with_archive(chat_tgid="-100")

    result = await chat_service.get_chat_with_archive(chat_tgid="-100")

    assert result is sample_chat
    mock_repo.get_chat_by_tgid.assert_called_once()


@pytest.mark.asyncio
async def test_get_or_create_race_condition_returns_existing(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """get_or_create при race condition (IntegrityError) повторно получает чат."""
    sample_chat.title = "New"
    mock_cache.get = AsyncMock(return_value=None)
    mock_repo.get_chat_by_tgid = AsyncMock(side_effect=[None, sample_chat])
    db_exc = DatabaseException("dup")
    db_exc.__cause__ = IntegrityError("", "", "")
    mock_repo.create_chat = AsyncMock(side_effect=db_exc)

    result = await chat_service.get_or_create(chat_tgid="-100", title="New")

    assert result is sample_chat
    mock_repo.create_chat.assert_called_once()
    assert mock_repo.get_chat_by_tgid.call_count == 2


@pytest.mark.asyncio
async def test_get_or_create_race_condition_raises_when_still_not_found(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """get_or_create при race condition пробрасывает исключение если чат не найден."""
    mock_cache.get = AsyncMock(return_value=None)
    mock_repo.get_chat_by_tgid = AsyncMock(return_value=None)
    db_exc = DatabaseException("dup")
    db_exc.__cause__ = IntegrityError("", "", "")
    mock_repo.create_chat = AsyncMock(side_effect=db_exc)

    with pytest.raises(DatabaseException):
        await chat_service.get_or_create(chat_tgid="-100", title="New")


@pytest.mark.asyncio
async def test_get_chat_from_repo_and_caches(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """get_chat при отсутствии в кеше загружает из репозитория и кеширует."""
    mock_cache.get = AsyncMock(return_value=None)
    mock_repo.get_chat_by_tgid = AsyncMock(return_value=sample_chat)

    result = await chat_service.get_chat(chat_tgid="-100")

    assert result is sample_chat
    mock_repo.get_chat_by_tgid.assert_called_once_with("-100")
    assert mock_cache.set.call_count >= 1


@pytest.mark.asyncio
async def test_create_chat_and_cache(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """create_chat создаёт чат и кеширует его."""
    mock_repo.create_chat = AsyncMock(return_value=sample_chat)

    result = await chat_service.create_chat(chat_tgid="-100", title="Test")

    assert result is sample_chat
    mock_repo.create_chat.assert_called_once_with(chat_id="-100", title="Test")
    mock_cache.set.assert_called()


@pytest.mark.asyncio
async def test_bind_archive_chat_success(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """bind_archive_chat привязывает архив и обновляет кеш."""
    archive_chat = MagicMock(spec=ChatSession)
    archive_chat.id = 2
    archive_chat.chat_id = "-200"
    archive_chat.title = "Archive"
    archive_chat.archive_chat_id = None
    sample_chat.archive_chat_id = "-200"
    sample_chat.archive_chat = archive_chat
    mock_repo.bind_archive_chat = AsyncMock(return_value=sample_chat)
    mock_repo.get_chat_by_tgid = AsyncMock(return_value=archive_chat)

    result = await chat_service.bind_archive_chat(
        work_chat_id=1,
        archive_chat_tgid="-200",
        archive_chat_title="Archive",
    )

    assert result is sample_chat
    mock_repo.bind_archive_chat.assert_called_once_with(
        work_chat_id=1,
        archive_chat_tgid="-200",
        archive_chat_title="Archive",
    )


@pytest.mark.asyncio
async def test_toggle_antibot_returns_new_state(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """toggle_antibot возвращает новое состояние is_antibot_enabled."""
    sample_chat.is_antibot_enabled = True
    mock_repo.toggle_antibot = AsyncMock(return_value=sample_chat)

    result = await chat_service.toggle_antibot(chat_id=1)

    assert result is True
    mock_repo.toggle_antibot.assert_called_once_with(chat_id=1)


@pytest.mark.asyncio
async def test_toggle_antibot_returns_none_when_chat_not_found(
    chat_service: ChatService,
    mock_repo: AsyncMock,
) -> None:
    """toggle_antibot возвращает None когда чат не найден."""
    mock_repo.toggle_antibot = AsyncMock(return_value=None)

    result = await chat_service.toggle_antibot(chat_id=999)

    assert result is None


@pytest.mark.asyncio
async def test_update_work_hours_success(
    chat_service: ChatService,
    mock_repo: AsyncMock,
    sample_chat: MagicMock,
) -> None:
    """update_work_hours обновляет рабочие часы и кеш."""
    sample_chat.start_time = time(10, 0)
    sample_chat.end_time = time(19, 0)
    mock_repo.update_work_hours = AsyncMock(return_value=sample_chat)

    result = await chat_service.update_work_hours(
        chat_id=1,
        start_time=time(10, 0),
        end_time=time(19, 0),
    )

    assert result is sample_chat
    mock_repo.update_work_hours.assert_called_once()
