import logging
from typing import List

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from keyboards.inline.chats_kb import template_scope_selector_kb
from keyboards.inline.templates_answers import templates_inline_kb
from models import ChatSession, MessageTemplate
from repositories import MessageTemplateRepository
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
    """Обрабчик выбора категории при создании нового шаблона"""

    category_id = int(query.data.split("__")[1])  # Парсим Id категории
    username = query.from_user.username

    logger.info(
        "Была выбрана категория id=%s пользователем - %s",
        category_id,
        query.from_user.username,
    )

    # Сохраняем выбранную категорию в состоянии
    await state.update_data(category_id=category_id)

    try:
        await state.set_state(TemplateStateManager.process_template_chat)

        chats = await get_chats_by_username(username=username)

        text = "Выбери группу для шаблона:"
        await query.message.answer(
            text=text,
            reply_markup=template_scope_selector_kb(chats=chats),
        )

    except Exception as e:
        logger.error("Ошибка при получении чатов: %s", e)
        await query.message.answer(str(e))
    finally:
        await query.answer()


async def get_chats_by_username(username: str) -> List[ChatSession]:
    try:
        usecase: GetTrackedChatsUseCase = container.resolve(GetTrackedChatsUseCase)
        chats = await usecase.execute(username=username)

        return chats
    except Exception as e:
        logger.error("Ошибка при получении чатов: %s", e)
        raise "Ошибка получения чатов!"


@router.callback_query(
    TemplateStateManager.listing_categories,
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
        total_count = await get_templates_count_by_category(
            category_id=int(category_id)
        )

        text = "Выберите шаблон:"

        await query.message.edit_text(
            text=text,
            reply_markup=templates_inline_kb(
                templates=templates,
                total_count=total_count,
            ),
        )

        await state.update_data(category_id=category_id)
        await state.set_state(TemplateStateManager.listing_templates)

        await query.answer()
    except Exception as e:
        logger.error("Ошибка при получении шаблонов: %s", e)
        await query.answer("Ошибка при получении шаблонов")


async def get_templates_by_category(category_id: int) -> List[MessageTemplate]:
    """Получает список шаблонов сообщений исходя из выбранной категории"""
    response_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )

    templates = await response_repo.get_templates_by_category_paginated(
        category_id=category_id,
    )

    return templates


async def get_templates_count_by_category(category_id: int) -> int:
    """Получает общее количество шаблонов"""
    template_repo: MessageTemplateRepository = container.resolve(
        MessageTemplateRepository
    )

    return await template_repo.get_templates_count_by_category(category_id)
