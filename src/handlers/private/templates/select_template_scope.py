import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants.pagination import TEMPLATES_PAGE_SIZE
from keyboards.inline.templates import templates_inline_kb, templates_menu_ikb
from services.templates import TemplateService
from states import TemplateStateManager
from utils.exception_handler import handle_exception
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == "template_scope_global",
    TemplateStateManager.selecting_template_scope,
)
async def select_global_templates_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик выбора глобальных шаблонов"""
    await callback.answer()

    try:
        template_service: TemplateService = container.resolve(TemplateService)
        templates = await template_service.get_global_templates_paginated(
            page=1,
            page_size=TEMPLATES_PAGE_SIZE,
        )
        total_count = await template_service.get_global_templates_count()

        if not templates:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❗ Глобальных шаблонов не найдено",
                reply_markup=templates_menu_ikb(),
            )
            await state.set_state(TemplateStateManager.templates_menu)
            return

        await state.update_data(template_scope="global")

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"Глобальные шаблоны ({total_count}):",
            reply_markup=templates_inline_kb(
                templates=templates,
                page=1,
                total_count=total_count,
            ),
        )

        await state.set_state(TemplateStateManager.listing_templates)

    except Exception as e:
        await handle_exception(callback.message, e, "select_global_templates_handler")


@router.callback_query(
    F.data.startswith("template_scope_chat__"),
    TemplateStateManager.selecting_template_scope,
)
async def select_chat_templates_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик выбора шаблонов для конкретного чата"""
    await callback.answer()

    chat_id = int(callback.data.split("__")[1])

    try:
        template_service: TemplateService = container.resolve(TemplateService)
        templates = await template_service.get_chat_templates_paginated(
            chat_id=chat_id,
            page=1,
            page_size=TEMPLATES_PAGE_SIZE,
        )
        total_count = await template_service.get_chat_templates_count(chat_id=chat_id)

        if not templates:
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="❗ Шаблонов для этого чата не найдено",
                reply_markup=templates_menu_ikb(),
            )
            await state.set_state(TemplateStateManager.templates_menu)
            return

        await state.update_data(template_scope="chat", chat_id=chat_id)

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"Шаблоны для чата ({total_count}):",
            reply_markup=templates_inline_kb(
                templates=templates,
                page=1,
                total_count=total_count,
            ),
        )

        await state.set_state(TemplateStateManager.listing_templates)

    except Exception as e:
        await handle_exception(callback.message, e, "select_chat_templates_handler")
