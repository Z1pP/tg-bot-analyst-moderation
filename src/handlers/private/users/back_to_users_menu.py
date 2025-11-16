from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from keyboards.inline.users import users_menu_ikb
from states import UserStateManager
from utils.state_logger import log_and_set_state

router = Router(name=__name__)


@router.callback_query(F.data == "users_menu")
async def back_to_users_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    await callback.message.edit_text(
        text="Выбери действие:",
        reply_markup=users_menu_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=UserStateManager.users_menu,
    )
