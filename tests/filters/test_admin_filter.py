"""Тесты для filters/admin_filter.py."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from aiogram.types import CallbackQuery, InlineQuery, Message
from aiogram.types import User as TgUser

from constants.enums import UserRole
from filters.admin_filter import AdminOnlyFilter, StaffOnlyFilter, StaffOnlyInlineFilter


def _make_user(
    role: UserRole, tg_id: str = "123", username: str = "user"
) -> SimpleNamespace:
    """Мок пользователя с полем role для проверки фильтров."""
    return SimpleNamespace(id=1, tg_id=tg_id, username=username, role=role)


def _make_message(user_id: int = 123, username: str | None = "user") -> Message:
    return Message.model_construct(
        message_id=1,
        date=MagicMock(),
        chat=MagicMock(),
        from_user=TgUser.model_construct(id=user_id, username=username),
    )


def _make_callback(user_id: int = 123, username: str | None = "user") -> CallbackQuery:
    return CallbackQuery.model_construct(
        id="cb1",
        from_user=TgUser.model_construct(id=user_id, username=username),
    )


@pytest.mark.asyncio
async def test_admin_only_filter_message_with_admin_user() -> None:
    """AdminOnlyFilter возвращает True для пользователя с ролью ADMIN."""
    flt = AdminOnlyFilter()
    container = MagicMock()
    user = _make_user(UserRole.ADMIN)
    flt.get_user = AsyncMock(return_value=user)
    msg = _make_message()

    result = await flt(msg, container)

    assert result is True


@pytest.mark.asyncio
async def test_admin_only_filter_message_with_regular_user_returns_false() -> None:
    """AdminOnlyFilter для обычного пользователя (user=None) вызывает answer и возвращает False."""
    flt = AdminOnlyFilter()
    container = MagicMock()
    flt.get_user = AsyncMock(return_value=None)
    msg = _make_message()
    with patch.object(Message, "answer", new_callable=AsyncMock) as mock_answer:
        result = await flt(msg, container)
    assert result is False
    mock_answer.assert_called_once()
    assert any("нет доступа" in str(a) for a in mock_answer.call_args[0])


@pytest.mark.asyncio
async def test_admin_only_filter_callback_query_with_root() -> None:
    """AdminOnlyFilter для CallbackQuery с пользователем ROOT возвращает True."""
    flt = AdminOnlyFilter()
    container = MagicMock()
    user = _make_user(UserRole.ROOT, username="root")
    flt.get_user = AsyncMock(return_value=user)
    cb = _make_callback()

    result = await flt(cb, container)

    assert result is True


@pytest.mark.asyncio
async def test_admin_only_filter_other_event_type_returns_false() -> None:
    """AdminOnlyFilter для не Message/CallbackQuery возвращает False."""
    flt = AdminOnlyFilter()
    container = MagicMock()
    flt.get_user = AsyncMock()

    result = await flt(MagicMock(), container)

    assert result is False
    flt.get_user.assert_not_called()


@pytest.mark.asyncio
async def test_staff_only_filter_with_moderator() -> None:
    """StaffOnlyFilter возвращает True для MODERATOR."""
    flt = StaffOnlyFilter()
    container = MagicMock()
    user = _make_user(UserRole.MODERATOR, username="mod")
    flt.get_user = AsyncMock(return_value=user)
    msg = _make_message()

    result = await flt(msg, container)

    assert result is True


@pytest.mark.asyncio
async def test_staff_only_filter_with_none_user_returns_false() -> None:
    """StaffOnlyFilter возвращает False, если пользователь не найден."""
    flt = StaffOnlyFilter()
    container = MagicMock()
    flt.get_user = AsyncMock(return_value=None)
    msg = _make_message()

    result = await flt(msg, container)

    assert result is False


@pytest.mark.asyncio
async def test_staff_only_inline_filter_with_dev() -> None:
    """StaffOnlyInlineFilter возвращает True для DEV."""
    flt = StaffOnlyInlineFilter()
    container = MagicMock()
    user = _make_user(UserRole.DEV, username="dev")
    flt.get_user = AsyncMock(return_value=user)
    inline = InlineQuery.model_construct(
        id="iq1",
        from_user=TgUser.model_construct(id=123, username="dev"),
        query="",
        offset="",
    )

    result = await flt(inline, container)

    assert result is True
