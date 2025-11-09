import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from keyboards.inline.templates import edit_template_kb
from repositories import MessageTemplateRepository
from states import TemplateStateManager
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

from .common import common_process_template_title_handler

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("edit_template__"))
async def edit_template_handler(query: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала редактирования шаблона"""
    try:
        template_id = int(query.data.split("__")[1])

        # Получаем шаблон из БД
        template_repo: MessageTemplateRepository = container.resolve(
            MessageTemplateRepository
        )
        template = await template_repo.get_template_by_id(template_id)

        if not template:
            await query.answer("Шаблон не найден", show_alert=True)
            return

        # Сохраняем данные шаблона в state
        await state.update_data(
            edit_template_id=template_id, original_title=template.title
        )

        await state.set_state(TemplateStateManager.editing_template)

        await send_html_message_with_kb(
            message=query.message,
            text=f"<b>Редактирование шаблона:</b> {template.title}\n\n"
            "Что вы хотите изменить?",
            reply_markup=edit_template_kb(),
        )

        logger.info(
            f"Начато редактирование шаблона {template_id} пользователем {query.from_user.username}"
        )

    except Exception as e:
        await handle_exception(query.message, e, "edit_template_callback")
    finally:
        await query.answer()


@router.callback_query(F.data == "edit_title", TemplateStateManager.editing_template)
async def edit_title_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик редактирования названия шаблона"""
    await common_process_template_title_handler(
        callback=callback,
        state=state,
    )


@router.callback_query(F.data == "edit_content", TemplateStateManager.editing_template)
async def edit_content_handler(query: CallbackQuery, state: FSMContext) -> None:
    """Обработчик редактирования содержимого шаблона"""
    try:
        await state.set_state(TemplateStateManager.editing_content)

        await query.message.edit_text(
            text="<b>Редактирование содержимого</b>\n\n"
            "Отправьте новое содержимое для шаблона или перешлите сообщение из чата "
            "(текст, фото или медиагруппу):"
        )

    except Exception as e:
        await handle_exception(query.message, e, "edit_content_callback")
    finally:
        await query.answer()


@router.callback_query(F.data == "cancel_edit", TemplateStateManager.editing_template)
async def cancel_edit_handler(query: CallbackQuery, state: FSMContext) -> None:
    """Обработчик отмены редактирования"""
    try:
        await state.set_state(TemplateStateManager.templates_menu)
        await state.update_data(edit_template_id=None, original_title=None)

        await query.message.edit_text(text="❌ Редактирование отменено")

    except Exception as e:
        await handle_exception(query.message, e, "cancel_edit_callback")
    finally:
        await query.answer()
