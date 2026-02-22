"""Тесты для filters/root_dev_filter.py."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.types import CallbackQuery, Message
from aiogram.types import User as TgUser

from constants.enums import UserRole
from filters.root_dev_filter import RootDevOnlyFilter


def _make_user(role: UserRole, username: str = "user") -> SimpleNamespace:
    return SimpleNamespace(id=1, tg_id="123", username=username, role=role)


def _make_message(user_id: int = 123, username: str | None = "user") -> Message:
    return Message.model_construct(
        message_id=1,
        date=None,
        chat=None,
        from_user=TgUser.model_construct(id=user_id, username=username),
    )


def _make_callback(user_id: int = 123) -> CallbackQuery:
    return CallbackQuery.model_construct(
        id="cb1",
        from_user=TgUser.model_construct(id=user_id, username="dev"),
    )


@pytest.mark.asyncio
async def test_root_dev_only_filter_message_with_dev_returns_true() -> None:
    """RootDevOnlyFilter для Message с пользователем DEV возвращает True."""
    flt = RootDevOnlyFilter()
    container = MagicMock()
    user = _make_user(UserRole.DEV, username="dev")
    flt.get_user = AsyncMock(return_value=user)
    msg = _make_message()

    result = await flt(msg, container)

    assert result is True


@pytest.mark.asyncio
async def test_root_dev_only_filter_message_with_admin_returns_false() -> None:
    """RootDevOnlyFilter для ADMIN возвращает False (только ROOT/DEV)."""
    flt = RootDevOnlyFilter()
    container = MagicMock()
    user = _make_user(UserRole.ADMIN, username="admin")
    flt.get_user = AsyncMock(return_value=user)
    msg = _make_message()

    result = await flt(msg, container)

    assert result is False


@pytest.mark.asyncio
async def test_root_dev_only_filter_callback_with_root_returns_true() -> None:
    """RootDevOnlyFilter для CallbackQuery с ROOT возвращает True."""
    flt = RootDevOnlyFilter()
    container = MagicMock()
    user = _make_user(UserRole.ROOT, username="root")
    flt.get_user = AsyncMock(return_value=user)
    cb = _make_callback()

    result = await flt(cb, container)

    assert result is True


@pytest.mark.asyncio
async def test_root_dev_only_filter_other_event_returns_false() -> None:
    """RootDevOnlyFilter для не Message/CallbackQuery возвращает False."""
    flt = RootDevOnlyFilter()
    container = MagicMock()

    result = await flt(MagicMock(), container)

    assert result is False
