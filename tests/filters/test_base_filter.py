"""Тесты для filters/base_filter.py."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from constants.enums import UserRole
from filters.admin_filter import AdminOnlyFilter
from models.user import User


@pytest.mark.asyncio
async def test_base_user_filter_get_user_resolves_service() -> None:
    """get_user резолвит UserService из контейнера и вызывает get_user."""
    filter_instance = AdminOnlyFilter()
    container = MagicMock()
    user = User(tg_id="123", username="test", role=UserRole.ADMIN)
    user_service = AsyncMock()
    user_service.get_user = AsyncMock(return_value=user)
    container.resolve = MagicMock(return_value=user_service)

    result = await filter_instance.get_user(
        tg_id="123",
        current_username="test",
        container=container,
    )

    assert result == user
    container.resolve.assert_called_once()
    user_service.get_user.assert_called_once_with(tg_id="123", username="test")


@pytest.mark.asyncio
async def test_base_user_filter_get_user_returns_none() -> None:
    """get_user возвращает None, если сервис вернул None."""
    filter_instance = AdminOnlyFilter()
    container = MagicMock()
    user_service = AsyncMock()
    user_service.get_user = AsyncMock(return_value=None)
    container.resolve = MagicMock(return_value=user_service)

    result = await filter_instance.get_user(
        tg_id="999",
        current_username=None,
        container=container,
    )

    assert result is None
