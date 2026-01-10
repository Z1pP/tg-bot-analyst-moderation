"""Базовый обработчик пагинации для устранения дублирования кода."""

from abc import ABC, abstractmethod
from typing import Any, List, Optional, Tuple

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from punq import Container


class BasePaginationHandler(ABC):
    """Базовый класс для обработчиков пагинации."""

    def __init__(self, entity_name: str):
        self.entity_name = entity_name

    async def handle_prev_page(
        self,
        query: CallbackQuery,
        state: FSMContext,
        container: Optional[Container] = None,
    ) -> None:
        """Обработчик перехода на предыдущую страницу."""
        current_page = int(query.data.split("__")[1])
        prev_page = max(1, current_page - 1)

        items, total_count = await self.get_page_data(
            prev_page, query, state, container
        )
        keyboard = await self.build_keyboard(items, prev_page, total_count)

        await query.message.edit_reply_markup(reply_markup=keyboard)
        await query.answer()

    async def handle_next_page(
        self,
        query: CallbackQuery,
        state: FSMContext,
        container: Optional[Container] = None,
    ) -> None:
        """Обработчик перехода на следующую страницу."""
        current_page = int(query.data.split("__")[1])
        next_page = current_page + 1

        items, total_count = await self.get_page_data(
            next_page, query, state, container
        )

        if not items:
            await query.answer(f"Больше {self.entity_name} нет")
            return

        keyboard = await self.build_keyboard(items, next_page, total_count)

        await query.message.edit_reply_markup(reply_markup=keyboard)
        await query.answer()

    @abstractmethod
    async def get_page_data(
        self,
        page: int,
        query: CallbackQuery,
        state: FSMContext,
        container: Optional[Container] = None,
    ) -> Tuple[List[Any], int]:
        """Получает данные для страницы. Должен быть реализован в наследниках."""
        pass

    @abstractmethod
    async def build_keyboard(
        self,
        items: List[Any],
        page: int,
        total_count: int,
    ) -> InlineKeyboardMarkup:
        """Строит клавиатуру для страницы. Должен быть реализован в наследниках."""
        pass
