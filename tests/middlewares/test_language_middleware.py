"""Тесты LanguageMiddleware: вызов next handler и установка user_language в data."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Message, User

from middlewares.language_middleware import LanguageMiddleware


@pytest.fixture
def mock_user_service() -> MagicMock:
    """Мок UserService."""
    svc = MagicMock()
    svc.get_user = AsyncMock(return_value=None)
    return svc


@pytest.fixture
def mock_container() -> MagicMock:
    """Мок контейнера (не используется в базовом сценарии без обновления языка)."""
    return MagicMock()


@pytest.fixture
def mock_handler() -> AsyncMock:
    """Мок следующего обработчика."""
    return AsyncMock(return_value="ok")


@pytest.fixture
def message_event() -> Message:
    """Message с from_user и language_code (нужен реальный тип для isinstance в middleware)."""
    return Message.model_construct(
        message_id=1,
        date=MagicMock(),
        chat=MagicMock(),
        from_user=User.model_construct(
            id=999,
            is_bot=False,
            first_name="Test",
            username="user",
            language_code="ru",
        ),
    )


@pytest.mark.asyncio
async def test_language_middleware_calls_handler_and_sets_user_language(
    mock_user_service: MagicMock,
    mock_container: MagicMock,
    mock_handler: AsyncMock,
    message_event: Message,
) -> None:
    """Middleware вызывает handler и записывает user_language в data."""
    mock_user_service.get_user = AsyncMock(return_value=None)
    middleware = LanguageMiddleware(
        user_service=mock_user_service,
        container=mock_container,
    )
    data = {}

    result = await middleware(mock_handler, message_event, data)

    mock_handler.assert_called_once_with(message_event, data)
    assert "user_language" in data
    assert data["user_language"] in ("ru", "en")
    assert result == "ok"
