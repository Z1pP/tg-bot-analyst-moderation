"""Тесты пагинации чатов в приватном меню."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from dto.chat_dto import ChatDTO
from handlers.private.chats import pagination


def _chat(index: int) -> ChatDTO:
    return ChatDTO(
        id=index,
        tg_id=str(-100 - index),
        title=f"chat{index}",
        is_antibot_enabled=False,
        is_auto_moderation_enabled=False,
    )


@pytest.mark.asyncio
async def test_get_tracked_chats_uses_tg_id() -> None:
    """Чаты запрашиваются по telegram id администратора, а не по username."""
    usecase = AsyncMock()
    usecase.execute.return_value = [_chat(1)]
    container = MagicMock()
    container.resolve.return_value = usecase

    result = await pagination.get_tracked_chats("123", container)

    usecase.execute.assert_awaited_once_with(tg_id="123")
    assert result == [_chat(1)]


def test_paginate_chats_slices_and_counts() -> None:
    """paginate_chats отдаёт срез страницы и общее количество."""
    chats = [_chat(i) for i in range(7)]

    page, total = pagination.paginate_chats(chats, page=2, page_size=3)

    assert page == chats[3:6]
    assert total == 7


@pytest.mark.asyncio
async def test_get_page_data_uses_callback_user_id() -> None:
    """Пагинатор берёт telegram id из callback, а не username."""
    usecase = AsyncMock()
    usecase.execute.return_value = [_chat(1)]
    container = MagicMock()
    container.resolve.return_value = usecase
    callback = MagicMock()
    callback.from_user.id = 42

    items, total = await pagination.ChatsPaginationHandler().get_page_data(
        1, callback, AsyncMock(), container
    )

    usecase.execute.assert_awaited_once_with(tg_id="42")
    assert items == [_chat(1)]
    assert total == 1