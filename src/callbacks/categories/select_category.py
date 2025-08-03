import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from keyboards.inline.chats_kb import template_scope_selector_kb
from keyboards.inline.templates_answers import templates_inline_kb
from services.templates import TemplateService
from states import TemplateStateManager
from usecases.chat import GetTrackedChatsUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    TemplateStateManager.process_template_category,
    F.data.startswith("category__"),
)
async def select_category_for_template_callback(
    query: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик выбора категории при создании нового шаблона"""
    category_id = int(query.data.split("__")[1])
    username = query.from_user.username

    logger.info(
        "Была выбрана категория id=%s пользователем - %s",
        category_id,
        username,
    )

    await state.update_data(category_id=category_id)
    await state.set_state(TemplateStateManager.process_template_chat)

    try:
        usecase: GetTrackedChatsUseCase = container.resolve(GetTrackedChatsUseCase)
        chats = await usecase.execute(username=username)
        await query.message.answer(
            text="Выбери группу для шаблона:",
            reply_markup=template_scope_selector_kb(chats=chats),
        )
    except Exception as e:
        logger.error("Ошибка при получении чатов: %s", e)
        await query.message.answer(f"Ошибка: {e}")
    finally:
        await query.answer()


@router.callback_query(
    TemplateStateManager.listing_categories,
    F.data.startswith("category__"),
)
async def show_templates_by_category_callback(
    query: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик выбора категории при просмотре шаблонов"""
    category_id = int(query.data.split("__")[1])

    logger.info(
        "Была выбрана категория id=%s пользователем - %s",
        category_id,
        query.from_user.username,
    )

    try:
        service: TemplateService = container.resolve(TemplateService)
        templates = await service.get_by_category(category_id=category_id)
        total_count = await service.get_count_by_category(category_id=category_id)

        await query.message.edit_text(
            text="Выберите шаблон:",
            reply_markup=templates_inline_kb(
                templates=templates,
                total_count=total_count,
                category_id=category_id,  # Передаем ID категории для пагинации
            ),
        )

        await state.update_data(category_id=category_id)
        await state.set_state(TemplateStateManager.listing_templates)
        await query.answer()
    except Exception as e:
        logger.error("Ошибка при получении шаблонов: %s", e)
        await query.answer("Ошибка при получении шаблонов")
