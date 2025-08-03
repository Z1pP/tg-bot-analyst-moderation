from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.reply.user_actions import user_actions_kb
from states.user_states import UserStateManager
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.callback_query(F.data.startswith("user__"))
async def user_selected_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик выбора пользователя из списка модераторов.
    """
    try:
        _, username = callback.data.split("__")

        await state.set_state(UserStateManager.viewing_user)
        await state.update_data(username=username)

        await send_html_message_with_kb(
            message=callback.message,
            text=f"Выбран пользователь: {username}",
            reply_markup=user_actions_kb(),
        )

        await callback.answer()

    except Exception as e:
        await handle_exception(
            message=callback.message, exc=e, context="user_selected_handler"
        )
