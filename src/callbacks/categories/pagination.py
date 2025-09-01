from typing import List, Tuple

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup

from constants.pagination import CATEGORIES_PAGE_SIZE
from container import container
from keyboards.inline.categories import categories_inline_kb
from models import TemplateCategory
from repositories import TemplateCategoryRepository
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
        categories = await get_categories_by_page(page=page)
        total_count = await get_categories_count()
        return categories, total_count

    async def build_keyboard(
        self,
        items: List[TemplateCategory],
        page: int,
        total_count: int,
    ) -> InlineKeyboardMarkup:
        return categories_inline_kb(
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


async def get_categories_by_page(
    page: int = 1,
    page_size: int = CATEGORIES_PAGE_SIZE,
) -> List[TemplateCategory]:
    category_repo: TemplateCategoryRepository = container.resolve(
        TemplateCategoryRepository
    )
    offset = (page - 1) * page_size
    return await category_repo.get_categories_paginated(limit=page_size, offset=offset)


async def get_categories_count() -> int:
    category_repo: TemplateCategoryRepository = container.resolve(
        TemplateCategoryRepository
    )
    return await category_repo.get_categories_count()
