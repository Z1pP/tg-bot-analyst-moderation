from typing import List, Optional

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from keyboards.inline.templates import templates_inline_kb
from models import MessageTemplate
from repositories import MessageTemplateRepository
from states import TemplateStateManager

router = Router(name=__name__)


@router.callback_query(
    TemplateStateManager.listing_templates,
    F.data.startswith("prev_page__"),
)
async def prev_page_templates_callback(query: CallbackQuery, state: FSMContext) -> None:
    """Обработчик перехода на предыдущую страницу шаблонов"""
    current_page = int(query.data.split("__")[1])
    prev_page = max(1, current_page - 1)
    category_id = await extract_category_id(state=state)

    if category_id:
        templates = await get_templates_by_category_page(
            page=prev_page,
            category_id=category_id,
        )
        total_count = await get_templates_count_by_category(category_id=category_id)
    else:
        templates = await get_templates_by_page(page=prev_page)
        total_count = await get_templates_count()

    await query.message.edit_reply_markup(
        reply_markup=templates_inline_kb(
            templates=templates,
            page=prev_page,
            total_count=total_count,
        )
    )
    await query.answer()


@router.callback_query(
    TemplateStateManager.listing_templates,
    F.data.startswith("next_page__"),
)
async def next_page_templates_callback(query: CallbackQuery, state: FSMContext) -> None:
    """Обработчик перехода на следующую страницу шаблонов"""
    current_page = int(query.data.split("__")[1])
    next_page = current_page + 1
    category_id = await extract_category_id(state=state)

    if category_id:
        templates = await get_templates_by_category_page(
            page=next_page,
            category_id=category_id,
        )
        total_count = await get_templates_count_by_category(category_id=category_id)
    else:
        templates = await get_templates_by_page(next_page)
        total_count = await get_templates_count()

    if not templates:
        await query.answer("Больше шаблонов нет")
        return

    await query.message.edit_reply_markup(
        reply_markup=templates_inline_kb(
            templates=templates,
            page=next_page,
            total_count=total_count,
        )
    )
    await query.answer()


async def get_templates_by_category_page(
    page: int = 1, category_id: int = None
) -> List[MessageTemplate]:
    """Получает шаблоны для указанной страницы и категории"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )

    offset = (page - 1) * 5
    templates = await template_repo.get_templates_by_category_paginated(
        category_id=category_id,
        limit=5,
        offset=offset,
    )
    return templates


async def get_templates_by_page(
    page: int = 1, page_size: int = 5
) -> List[MessageTemplate]:
    """Получает шаблоны для указанной страницы"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )

    offset = (page - 1) * page_size
    templates = await template_repo.get_templates_paginated(
        limit=page_size,
        offset=offset,
    )
    return templates


async def get_templates_count() -> int:
    """Получает общее количество шаблонов"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )
    return await template_repo.get_templates_count()


async def get_templates_count_by_category(category_id: int) -> int:
    """Получает общее количество шаблонов"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )

    return await template_repo.get_templates_count_by_category(category_id)


async def extract_category_id(state: FSMContext) -> Optional[int]:
    data = await state.get_data()
    category_id = data.get("category_id", None)

    if category_id:
        return int(category_id)
