from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from keyboards.reply.user_actions import user_actions_kb
from states import AllUsersReportStates
from utils.exception_handler import handle_exception
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)


@router.callback_query(F.data == "all_users")
async def all_users_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик команды для получения списка всех пользователей.
    """
    try:
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=AllUsersReportStates.selected_all_users,
        )
        await send_html_message_with_kb(
            message=callback.message,
            text="Выбери действие:",
            reply_markup=user_actions_kb(),
        )

    except Exception as e:
        await handle_exception(
            message=callback.message, exc=e, context="all_users_handler"
        )
        await state.clear()
