from typing import List, Tuple

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from constants.pagination import CATEGORIES_PAGE_SIZE
from container import container
from keyboards.inline.categories import categories_inline_ikb
from models import TemplateCategory
from usecases.categories import GetCategoriesPaginatedUseCase
from utils.pagination_handler import BasePaginationHandler

router = Router(name=__name__)


class CategoriesPaginationHandler(BasePaginationHandler):
    def __init__(self):
        super().__init__("категорий")

    async def get_page_data(
        self,
        page: int,
        query: CallbackQuery,
        state: FSMContext,
    ) -> Tuple[List[TemplateCategory], int]:
        usecase: GetCategoriesPaginatedUseCase = container.resolve(
            GetCategoriesPaginatedUseCase
        )
        offset = (page - 1) * CATEGORIES_PAGE_SIZE
        return await usecase.execute(limit=CATEGORIES_PAGE_SIZE, offset=offset)

    async def build_keyboard(
        self,
        items: List[TemplateCategory],
        page: int,
        total_count: int,
    ) -> InlineKeyboardMarkup:
        return categories_inline_ikb(
            categories=items,
            page=page,
            total_count=total_count,
        )


handler = CategoriesPaginationHandler()


@router.callback_query(F.data.startswith("prev_categories_page__"))
async def prev_categories_page_callback(
    query: CallbackQuery,
    state: FSMContext,
) -> None:
    await handler.handle_prev_page(query, state)


@router.callback_query(F.data.startswith("next_categories_page__"))
async def next_categories_page_callback(
    query: CallbackQuery,
    state: FSMContext,
) -> None:
    await handler.handle_next_page(query, state)
