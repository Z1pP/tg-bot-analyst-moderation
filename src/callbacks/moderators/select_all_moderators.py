from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.reply.user_actions import get_all_users_actions_kb
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.callback_query(F.data == "all_users")
async def all_users_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик команды для получения списка всех пользователей.
    """
    try:
        await state.clear()
        await send_html_message_with_kb(
            message=callback.message,
            text="Выбрано: все модераторы",
            reply_markup=get_all_users_actions_kb(),
        )

    except Exception as e:
        await handle_exception(
            message=callback.message, exc=e, context="all_users_handler"
        )
        await state.clear()
