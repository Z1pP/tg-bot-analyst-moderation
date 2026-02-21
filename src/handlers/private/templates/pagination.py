from dataclasses import dataclass
from typing import List, Optional, Tuple

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants.pagination import TEMPLATES_PAGE_SIZE
from dto.template_dto import GetTemplatesPaginatedDTO
from keyboards.inline.templates import templates_inline_kb
from models import MessageTemplate
from states import TemplateStateManager
from usecases.templates import GetTemplatesPaginatedUseCase
from utils.send_message import safe_edit_message

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
async def prev_page_templates_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик перехода на предыдущую страницу шаблонов"""
    current_page = int(callback.data.split("__")[1])
    prev_page = max(1, current_page - 1)
    state_data = await extract_state_data(state=state)

    templates, total_count = await get_templates_and_count(
        data=state_data,
        page=prev_page,
        container=container,
    )

    await callback.message.edit_reply_markup(
        reply_markup=templates_inline_kb(
            templates=templates,
            page=prev_page,
            total_count=total_count,
            show_back_to_categories=state_data.category_id is not None,
        )
    )
    await callback.answer()


@router.callback_query(
    TemplateStateManager.listing_templates,
    F.data.startswith("next_page__"),
)
async def next_page_templates_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик перехода на следующую страницу шаблонов"""
    current_page = int(callback.data.split("__")[1])
    next_page = current_page + 1
    state_data = await extract_state_data(state=state)

    templates, total_count = await get_templates_and_count(
        data=state_data,
        page=next_page,
        container=container,
    )

    if not templates:
        # Получаем текущую клавиатуру для сохранения кнопки возврата
        state_data = await extract_state_data(state=state)
        # Получаем предыдущую страницу для отображения
        prev_templates, total_count = await get_templates_and_count(
            data=state_data,
            page=current_page,
            container=container,
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="ℹ️ Больше шаблонов нет",
            reply_markup=templates_inline_kb(
                templates=prev_templates,
                page=current_page,
                total_count=total_count,
                show_back_to_categories=state_data.category_id is not None,
            ),
        )
        await callback.answer()
        return

    await callback.message.edit_reply_markup(
        reply_markup=templates_inline_kb(
            templates=templates,
            page=next_page,
            total_count=total_count,
            show_back_to_categories=state_data.category_id is not None,
        )
    )
    await callback.answer()


async def get_templates_and_count(
    data: StateDataExtractor,
    container: Container,
    page: int = 1,
) -> Tuple[List[MessageTemplate], int]:
    """Получает шаблоны и общее количество через use case."""
    usecase: GetTemplatesPaginatedUseCase = container.resolve(
        GetTemplatesPaginatedUseCase
    )
    return await usecase.execute(
        GetTemplatesPaginatedDTO(
            category_id=data.category_id,
            chat_id=data.chat_id,
            page=page,
            page_size=TEMPLATES_PAGE_SIZE,
        )
    )


async def extract_state_data(state: FSMContext) -> StateDataExtractor:
    data = await state.get_data()

    return StateDataExtractor(
        category_id=int(data["category_id"]) if data.get("category_id") else None,
        chat_id=int(data["chat_id"]) if data.get("chat_id") else None,
        template_scope=data.get("template_scope"),
    )
