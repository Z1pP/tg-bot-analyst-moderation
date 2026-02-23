"""Тесты AdminAntispamMiddleware: вызов next handler, блокировка при муте."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import Message, User

from middlewares.admin_antispam import AdminAntispamMiddleware


@pytest.fixture
def mock_cache() -> MagicMock:
    """Мок кеша (не Redis): get/set, без exists/increment."""
    cache = MagicMock()
    cache.exists = AsyncMock(return_value=False)
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.increment = AsyncMock(return_value=1)
    return cache


@pytest.fixture
def mock_handler() -> AsyncMock:
    """Мок следующего обработчика в цепочке."""
    return AsyncMock(return_value="handled")


@pytest.fixture
def message_event() -> Message:
    """Message от админа (реальный тип для isinstance в middleware)."""
    return Message.model_construct(
        message_id=1,
        date=MagicMock(),
        chat=MagicMock(),
        from_user=User.model_construct(
            id=12345,
            is_bot=False,
            first_name="Admin",
        ),
    )


@pytest.mark.asyncio
async def test_admin_antispam_non_message_calls_handler(
    mock_cache: MagicMock,
    mock_handler: AsyncMock,
) -> None:
    """Если event не Message — middleware вызывает handler и возвращает результат."""
    middleware = AdminAntispamMiddleware(cache=mock_cache)
    event = MagicMock()  # не Message
    data = {}

    result = await middleware(mock_handler, event, data)

    mock_handler.assert_called_once_with(event, data)
    assert result == "handled"


@pytest.mark.asyncio
async def test_admin_antispam_message_calls_handler_when_not_muted(
    mock_cache: MagicMock,
    mock_handler: AsyncMock,
    message_event: MagicMock,
) -> None:
    """При сообщении от админа и отсутствии мута вызывается handler."""
    mock_cache.get = AsyncMock(return_value=None)
    middleware = AdminAntispamMiddleware(cache=mock_cache)
    data = {}

    result = await middleware(mock_handler, message_event, data)

    mock_handler.assert_called_once_with(message_event, data)
    assert result == "handled"


@pytest.mark.asyncio
async def test_admin_antispam_muted_returns_none(
    mock_cache: MagicMock,
    mock_handler: AsyncMock,
    message_event: MagicMock,
) -> None:
    """Если админ в муте — handler не вызывается, возвращается None."""
    mock_cache.get = AsyncMock(return_value="1")
    middleware = AdminAntispamMiddleware(cache=mock_cache)
    data = {}

    result = await middleware(mock_handler, message_event, data)

    mock_handler.assert_not_called()
    assert result is None
