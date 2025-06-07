from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.reply.chat_actions import all_chats_actions_kb
from states import ChatStateManager
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.callback_query(F.data == "all_chats")
async def all_chats_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик команды для получения списка всех чатов.
    """
    try:
        await state.set_state(ChatStateManager.selecting_all_chats)
        await state.update_data(chat_title="all")

        await send_html_message_with_kb(
            message=callback.message,
            text="Выбрано: все чаты",
            reply_markup=all_chats_actions_kb(),
        )

    except Exception as e:
        await handle_exception(
            message=callback.message, exc=e, context="all_chats_handler"
        )
