"""Тесты для filters/group_filter.py."""

from unittest.mock import MagicMock

import pytest
from aiogram.types import CallbackQuery, Chat, Message
from aiogram.types import User as TgUser

from filters.group_filter import ChatTypeFilter, GroupTypeFilter


def _make_message(chat_type: str = "private") -> Message:
    return Message.model_construct(
        message_id=1,
        date=MagicMock(),
        chat=Chat.model_construct(type=chat_type),
        from_user=TgUser.model_construct(id=1),
    )


def _make_callback(chat_type: str = "private") -> CallbackQuery:
    msg = Message.model_construct(
        message_id=1,
        date=MagicMock(),
        chat=Chat.model_construct(type=chat_type),
        from_user=TgUser.model_construct(id=1),
    )
    return CallbackQuery.model_construct(
        id="cb1",
        from_user=TgUser.model_construct(id=1),
        message=msg,
    )


@pytest.mark.asyncio
async def test_group_type_filter_default_matches_group() -> None:
    """GroupTypeFilter по умолчанию пропускает group и supergroup."""
    flt = GroupTypeFilter()
    msg = _make_message(chat_type="supergroup")

    result = await flt(msg)

    assert result is True


@pytest.mark.asyncio
async def test_group_type_filter_private_returns_false() -> None:
    """GroupTypeFilter с default не пропускает private."""
    flt = GroupTypeFilter()
    msg = _make_message(chat_type="private")

    result = await flt(msg)

    assert result is False


@pytest.mark.asyncio
async def test_chat_type_filter_message_private() -> None:
    """ChatTypeFilter по умолчанию пропускает private."""
    flt = ChatTypeFilter()
    msg = _make_message(chat_type="private")

    result = await flt(msg)

    assert result is True


@pytest.mark.asyncio
async def test_chat_type_filter_callback_private() -> None:
    """ChatTypeFilter для CallbackQuery проверяет message.chat.type."""
    flt = ChatTypeFilter()
    cb = _make_callback(chat_type="private")

    result = await flt(cb)

    assert result is True


@pytest.mark.asyncio
async def test_chat_type_filter_callback_group_returns_false() -> None:
    """ChatTypeFilter с default [PRIVATE] не пропускает group в callback."""
    flt = ChatTypeFilter()
    cb = _make_callback(chat_type="supergroup")

    result = await flt(cb)

    assert result is False


@pytest.mark.asyncio
async def test_chat_type_filter_other_event_returns_false() -> None:
    """ChatTypeFilter для не Message/CallbackQuery возвращает False."""
    flt = ChatTypeFilter()

    result = await flt(MagicMock())

    assert result is False
