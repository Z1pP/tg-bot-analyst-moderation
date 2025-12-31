from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants.callback import CallbackData
from keyboards.inline.users import users_menu_ikb
from states import UserStateManager

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.User.USERS_MENU)
async def back_to_users_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()

    await callback.message.edit_text(
        text="Выбери действие:",
        reply_markup=users_menu_ikb(),
    )

    await state.set_state(UserStateManager.users_menu)
