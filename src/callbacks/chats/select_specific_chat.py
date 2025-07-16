from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.reply.chat_actions import chat_actions_kb
from states import ChatStateManager, TemplateStateManager
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.callback_query(F.data.startswith("chat__"))
async def chat_selected_handler(
    query: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик выбора чата из списка чатов.
    """
    try:
        _, chat_title = query.data.split("__")

        await state.set_state(ChatStateManager.selecting_chat)
        await state.update_data(chat_title=chat_title)

        await send_html_message_with_kb(
            message=query.message,
            text=f"Выбран чат: {chat_title}",
            reply_markup=chat_actions_kb(chat_title=chat_title),
        )

        await query.answer()

    except Exception as e:
        await handle_exception(
            message=query.message, exc=e, context="chat_selected_handler"
        )


@router.callback_query(
    TemplateStateManager.process_template_chat,
    F.data.startswith("template_scope__"),
)
async def process_template_chat_handler(
    query: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик выбора чата из списка чатов.
    """
    try:
        chat_id = int(query.data.split("__")[1])

        await state.set_state(TemplateStateManager.process_template_title)

        if chat_id == -1:
            await state.update_data(chat_id=None)
        else:
            await state.update_data(chat_id=int(chat_id))

        text = "Укажите название шаблона:"

        await query.message.answer(text=text)

        await query.answer()

    except Exception as e:
        await handle_exception(
            message=query.message,
            exc=e,
            context="process_template_chat_handler",
        )
