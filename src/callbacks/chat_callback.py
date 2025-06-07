from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.reply.chat_actions import chat_actions_kb
from states import ChatStateManager
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.callback_query(F.data.startswith("chat__"))
async def chat_selected_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик выбора чата из списка чатов.
    """
    try:
        _, chat_title = callback.data.split("__")

        await state.set_state(ChatStateManager.selecting_chat)
        await state.update_data(chat_title=chat_title)

        await send_html_message_with_kb(
            message=callback.message,
            text=f"Выбран чат: {chat_title}",
            reply_markup=chat_actions_kb(chat_title=chat_title),
        )

        await callback.answer()

    except Exception as e:
        await handle_exception(
            message=callback.message, exc=e, context="chat_selected_handler"
        )
