from dataclasses import dataclass
from typing import List, Optional, Tuple

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from keyboards.inline.templates import templates_inline_kb
from models import MessageTemplate
from repositories import MessageTemplateRepository
from states import TemplateStateManager

router = Router(name=__name__)


@dataclass(frozen=True)
class StateDataExtractor:
    category_id: Optional[int] = None
    chat_id: Optional[int] = None
    template_scope: Optional[str] = None


@router.callback_query(
    TemplateStateManager.listing_templates,
    F.data.startswith("prev_page__"),
)
async def prev_page_templates_callback(query: CallbackQuery, state: FSMContext) -> None:
    """Обработчик перехода на предыдущую страницу шаблонов"""
    current_page = int(query.data.split("__")[1])
    prev_page = max(1, current_page - 1)
    state_data = await extract_state_data(state=state)

    templates, total_count = await get_templates_and_count(
        data=state_data,
        page=prev_page,
    )

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
    state_data = await extract_state_data(state=state)

    templates, total_count = await get_templates_and_count(
        data=state_data,
        page=next_page,
    )

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


async def get_templates_and_count(
    data: StateDataExtractor,
    page: int = 1,
) -> Tuple[List[MessageTemplate], int]:
    if data.chat_id:
        templates = await get_templates_by_chat_page(
            page=page,
            chat_id=data.chat_id,
        )
        total_count = await get_templates_count_by_chat(chat_id=data.chat_id)
    elif data.category_id:
        templates = await get_templates_by_category_page(
            page=page,
            category_id=data.category_id,
        )
        total_count = await get_templates_count_by_category(
            category_id=data.category_id
        )
    else:
        templates = await get_global_templates(page)
        total_count = await get_global_templates_count()

    return templates, total_count


async def get_templates_by_category_page(
    page: int = 1,
    category_id: int = None,
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


async def get_templates_count_by_category(category_id: int) -> int:
    """Получает общее количество шаблонов по категории"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )
    return await template_repo.get_templates_count_by_category(category_id)


async def get_templates_by_chat_page(
    page: int = 1,
    chat_id: int = None,
) -> List[MessageTemplate]:
    """Получает шаблоны для указанной страницы и чата"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )
    offset = (page - 1) * 5
    templates = await template_repo.get_chat_templates_paginated(
        chat_id=chat_id,
        limit=5,
        offset=offset,
    )
    return templates


async def get_templates_count_by_chat(chat_id: int) -> int:
    """Получает общее количество шаблонов по чату"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )
    return await template_repo.get_chat_templates_count(chat_id)


async def get_global_templates(page: int = 1) -> List[MessageTemplate]:
    """Получает глобальные шаблоны для указанной страницы"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )
    offset = (page - 1) * 5
    templates = await template_repo.get_global_templates_paginated(
        limit=5,
        offset=offset,
    )
    return templates


async def get_global_templates_count() -> int:
    """Получает общее количество глобальных шаблонов"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )
    return await template_repo.get_global_templates_count()


async def extract_state_data(state: FSMContext) -> StateDataExtractor:
    data = await state.get_data()

    return StateDataExtractor(
        category_id=int(data["category_id"]) if data.get("category_id") else None,
        chat_id=int(data["chat_id"]) if data.get("chat_id") else None,
        template_scope=data.get("template_scope"),
    )
