from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants.callback import CallbackData
from keyboards.inline.users import all_users_actions_ikb
from states import AllUsersReportStates
from utils.exception_handler import handle_exception

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.User.ALL_USERS)
async def all_users_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик команды для получения списка всех пользователей.
    """
    try:
        await callback.answer()
        await state.set_state(AllUsersReportStates.selected_all_users)
        await callback.message.edit_text(
            text="Выбери действие:",
            reply_markup=all_users_actions_ikb(),
        )

    except Exception as e:
        await handle_exception(
            message=callback.message, exc=e, context="all_users_handler"
        )
        await state.clear()
