"""Тесты для utils/pagination_handler.py."""

from unittest.mock import AsyncMock

import pytest
from aiogram.types import InlineKeyboardMarkup

from utils.pagination_handler import BasePaginationHandler


class ConcretePaginationHandler(BasePaginationHandler):
    """Конкретная реализация для тестов."""

    async def get_page_data(self, page, query, state, container=None):
        if page == 1:
            return [{"id": 1}], 1
        return [], 1

    async def build_keyboard(self, items, page, total_count):
        return InlineKeyboardMarkup(inline_keyboard=[])


@pytest.mark.asyncio
async def test_handle_prev_page() -> None:
    """handle_prev_page уменьшает страницу и обновляет клавиатуру."""
    handler = ConcretePaginationHandler(entity_name="items")
    query = AsyncMock()
    query.data = "pag__2"
    query.message = AsyncMock()
    query.message.edit_reply_markup = AsyncMock()
    query.answer = AsyncMock()
    state = AsyncMock()
    container = None

    await handler.handle_prev_page(query, state, container)

    query.message.edit_reply_markup.assert_called_once()
    query.answer.assert_called_once()


@pytest.mark.asyncio
async def test_handle_next_page_has_items() -> None:
    """handle_next_page при наличии данных обновляет клавиатуру."""
    # next_page = 1 при data "pag__0", get_page_data(1) возвращает непустой список
    handler = ConcretePaginationHandler(entity_name="items")
    query = AsyncMock()
    query.data = "pag__0"
    query.message = AsyncMock()
    query.message.edit_reply_markup = AsyncMock()
    query.answer = AsyncMock()
    state = AsyncMock()

    await handler.handle_next_page(query, state, None)

    query.message.edit_reply_markup.assert_called_once()
    query.answer.assert_called_once()


@pytest.mark.asyncio
async def test_handle_next_page_no_items_answers_only() -> None:
    """handle_next_page при пустой странице только answer с текстом 'Больше ... нет'."""
    handler = ConcretePaginationHandler(entity_name="items")
    query = AsyncMock()
    query.data = "pag__2"
    query.message = AsyncMock()
    query.answer = AsyncMock()
    state = AsyncMock()

    await handler.handle_next_page(query, state, None)

    query.message.edit_reply_markup.assert_not_called()
    query.answer.assert_called_once_with("Больше items нет")
