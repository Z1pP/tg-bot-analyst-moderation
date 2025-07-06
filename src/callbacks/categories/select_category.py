import logging
from typing import List

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from keyboards.inline.templates_answers import templates_inline_kb
from models import MessageTemplate
from repositories import MessageTemplateRepository
from states.response_state import QuickResponseStateManager

router = Router(name=__name__)

logger = logging.getLogger(__name__)


@router.callback_query(
    QuickResponseStateManager.process_template_category,
    F.data.startswith("category__"),
)
async def select_category_for_template_callback(
    query: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обрабчик выбора категории при создании нового шаблона"""

    category_id = query.data.split("__")[1]

    logger.info(
        "Была выбрана категория id=%s пользователем - %s",
        category_id,
        query.from_user.username,
    )

    # Сохраняем выбранную категорию в состоянии
    await state.update_data(category_id=category_id)

    text = "Введите название шаблона:"

    await query.message.answer(text=text)

    await state.set_state(QuickResponseStateManager.process_template_title)

    await query.answer()


@router.callback_query(
    QuickResponseStateManager.listing_categories,
    F.data.startswith("category__"),
)
async def show_templates_by_category_callback(
    query: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обрабчик выбора категории при просмотре шаблонов"""

    category_id = query.data.split("__")[1]

    logger.info(
        "Была выбрана категория id=%s пользователем - %s",
        category_id,
        query.from_user.username,
    )

    try:
        templates = await get_templates_by_category(category_id=int(category_id))

        text = "Выберите шаблон:"

        await query.message.edit_text(
            text=text,
            reply_markup=templates_inline_kb(templates=templates),
        )

        await state.set_state(QuickResponseStateManager.listing_templates)

        await query.answer()
    except Exception as e:
        logger.error("Ошибка при получении шаблонов: %s", e)
        await query.answer("Ошибка при получении шаблонов")


async def get_templates_by_category(category_id: int) -> List[MessageTemplate]:
    """Получает список шаблонов сообщений исходя из выбранной категории"""
    response_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )

    templates = await response_repo.get_templates_by_category(
        category_id=category_id,
    )

    return templates
