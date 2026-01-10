import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.users import users_menu_ikb
from states import UserStateManager
from utils.send_message import safe_edit_message

from ..common.navigation import show_main_menu

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.User.USERS_MENU)
async def users_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик меню пользователей"""
    await callback.answer()
    await state.clear()

    message_text = Dialog.User.SELECT_ACTION

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=message_text,
        reply_markup=users_menu_ikb(),
    )

    await state.set_state(UserStateManager.users_menu)


@router.callback_query(F.data == CallbackData.User.BACK_TO_MAIN_MENU_FROM_USERS)
async def back_to_main_menu_from_users_handler(
    callback: types.CallbackQuery, state: FSMContext, user_language: str
) -> None:
    """Обработчик возврата в главное меню из меню пользователей"""
    await callback.answer()
    await show_main_menu(
        callback=callback,
        state=state,
        user_language=user_language,
    )
