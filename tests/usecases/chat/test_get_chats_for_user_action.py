"""Тесты GetChatsForUserActionUseCase."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
)

from dto import ChatDTO
from usecases.chat.get_chats_for_user_action import GetChatsForUserActionUseCase


@pytest.fixture
def mock_user_service() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_chat_tracking_repository() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_bot_permission_service() -> MagicMock:
    return MagicMock()


@pytest.fixture
def usecase(
    mock_user_service: AsyncMock,
    mock_chat_tracking_repository: AsyncMock,
    mock_bot_permission_service: MagicMock,
) -> GetChatsForUserActionUseCase:
    return GetChatsForUserActionUseCase(
        user_service=mock_user_service,
        chat_tracking_repository=mock_chat_tracking_repository,
        bot_permission_service=mock_bot_permission_service,
    )


@pytest.fixture
def sample_chat() -> MagicMock:
    """Чат для ChatDTO.from_model."""
    chat = MagicMock()
    chat.id = 1
    chat.chat_id = "-100"
    chat.title = "Test Chat"
    chat.settings = MagicMock()
    chat.settings.is_antibot_enabled = False
    chat.settings.welcome_text = None
    return chat


@pytest.mark.asyncio
async def test_execute_admin_not_found_returns_empty(
    usecase: GetChatsForUserActionUseCase,
    mock_user_service: AsyncMock,
) -> None:
    """execute возвращает пустой список когда админ не найден."""
    mock_user_service.get_user = AsyncMock(return_value=None)

    result = await usecase.execute(admin_tgid="admin1", user_tgid="user1")

    assert result == []
    mock_user_service.get_user.assert_called_once_with(tg_id="admin1")


@pytest.mark.asyncio
async def test_execute_no_tracked_chats_returns_empty(
    usecase: GetChatsForUserActionUseCase,
    mock_user_service: AsyncMock,
    mock_chat_tracking_repository: AsyncMock,
) -> None:
    """execute возвращает пустой список когда нет отслеживаемых чатов."""
    admin = MagicMock()
    admin.id = 1
    mock_user_service.get_user = AsyncMock(return_value=admin)
    mock_chat_tracking_repository.get_all_tracked_chats = AsyncMock(
        return_value=[]
    )

    result = await usecase.execute(admin_tgid="admin1", user_tgid="user1")

    assert result == []


@pytest.mark.asyncio
async def test_execute_member_in_chat_appends_to_result(
    usecase: GetChatsForUserActionUseCase,
    mock_user_service: AsyncMock,
    mock_chat_tracking_repository: AsyncMock,
    mock_bot_permission_service: MagicMock,
    sample_chat: MagicMock,
) -> None:
    """execute добавляет чат в результат когда пользователь — член группы."""
    admin = MagicMock()
    admin.id = 1
    mock_user_service.get_user = AsyncMock(return_value=admin)
    mock_chat_tracking_repository.get_all_tracked_chats = AsyncMock(
        return_value=[sample_chat]
    )
    member = MagicMock()
    member.status = "member"
    mock_bot_permission_service.bot.get_chat_member = AsyncMock(
        return_value=member
    )

    result = await usecase.execute(admin_tgid="admin1", user_tgid="12345")

    assert len(result) == 1
    assert isinstance(result[0], ChatDTO)
    mock_bot_permission_service.bot.get_chat_member.assert_called_once_with(
        chat_id=sample_chat.chat_id, user_id=12345
    )


@pytest.mark.asyncio
async def test_execute_member_kicked_skips_chat(
    usecase: GetChatsForUserActionUseCase,
    mock_user_service: AsyncMock,
    mock_chat_tracking_repository: AsyncMock,
    mock_bot_permission_service: MagicMock,
    sample_chat: MagicMock,
) -> None:
    """execute не добавляет чат когда пользователь kicked."""
    admin = MagicMock()
    admin.id = 1
    mock_user_service.get_user = AsyncMock(return_value=admin)
    mock_chat_tracking_repository.get_all_tracked_chats = AsyncMock(
        return_value=[sample_chat]
    )
    member = MagicMock()
    member.status = "kicked"
    mock_bot_permission_service.bot.get_chat_member = AsyncMock(
        return_value=member
    )

    result = await usecase.execute(admin_tgid="admin1", user_tgid="12345")

    assert result == []


@pytest.mark.asyncio
async def test_execute_telegram_bad_request_continues(
    usecase: GetChatsForUserActionUseCase,
    mock_user_service: AsyncMock,
    mock_chat_tracking_repository: AsyncMock,
    mock_bot_permission_service: MagicMock,
    sample_chat: MagicMock,
) -> None:
    """execute пропускает чат при TelegramBadRequest (пользователь не в чате)."""
    admin = MagicMock()
    admin.id = 1
    mock_user_service.get_user = AsyncMock(return_value=admin)
    mock_chat_tracking_repository.get_all_tracked_chats = AsyncMock(
        return_value=[sample_chat]
    )
    mock_bot_permission_service.bot.get_chat_member = AsyncMock(
        side_effect=TelegramBadRequest(MagicMock(), "User not found")
    )

    result = await usecase.execute(admin_tgid="admin1", user_tgid="12345")

    assert result == []


@pytest.mark.asyncio
async def test_execute_telegram_forbidden_continues(
    usecase: GetChatsForUserActionUseCase,
    mock_user_service: AsyncMock,
    mock_chat_tracking_repository: AsyncMock,
    mock_bot_permission_service: MagicMock,
    sample_chat: MagicMock,
) -> None:
    """execute пропускает чат при TelegramForbiddenError."""
    admin = MagicMock()
    admin.id = 1
    mock_user_service.get_user = AsyncMock(return_value=admin)
    mock_chat_tracking_repository.get_all_tracked_chats = AsyncMock(
        return_value=[sample_chat]
    )
    mock_bot_permission_service.bot.get_chat_member = AsyncMock(
        side_effect=TelegramForbiddenError(MagicMock(), "Forbidden")
    )

    result = await usecase.execute(admin_tgid="admin1", user_tgid="12345")

    assert result == []


@pytest.mark.asyncio
async def test_execute_telegram_api_error_continues(
    usecase: GetChatsForUserActionUseCase,
    mock_user_service: AsyncMock,
    mock_chat_tracking_repository: AsyncMock,
    mock_bot_permission_service: MagicMock,
    sample_chat: MagicMock,
) -> None:
    """execute пропускает чат при TelegramAPIError (flood control и др.)."""
    admin = MagicMock()
    admin.id = 1
    mock_user_service.get_user = AsyncMock(return_value=admin)
    mock_chat_tracking_repository.get_all_tracked_chats = AsyncMock(
        return_value=[sample_chat]
    )
    mock_bot_permission_service.bot.get_chat_member = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "Too many requests")
    )

    result = await usecase.execute(admin_tgid="admin1", user_tgid="12345")

    assert result == []
