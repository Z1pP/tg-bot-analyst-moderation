from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants.callback import CallbackData
from keyboards.inline.users import all_users_actions_ikb
from states import AllUsersReportStates
from utils.exception_handler import handle_exception
from utils.send_message import safe_edit_message

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.User.ALL_USERS)
async def all_users_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик команды для получения списка всех пользователей.
    """
    try:
        await callback.answer()
        await state.set_state(AllUsersReportStates.selected_all_users)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text="Выбери действие:",
            reply_markup=all_users_actions_ikb(),
        )

    except Exception as e:
        await handle_exception(
            message=callback.message, exc=e, context="all_users_handler"
        )
        await state.clear()
