import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from keyboards.inline.users import users_menu_ikb
from keyboards.reply.menu import admin_menu_kb
from states import MenuStates, UserStateManager
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == "users_menu")
async def users_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик меню пользователей"""
    await callback.answer()
    await state.clear()

    message_text = Dialog.User.SELECT_ACTION

    await callback.message.edit_text(
        text=message_text,
        reply_markup=users_menu_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=UserStateManager.users_menu,
    )


@router.callback_query(F.data == "back_to_main_menu_from_users")
async def back_to_main_menu_from_users_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата в главное меню из меню пользователей"""
    await callback.answer()
    await state.clear()

    username = callback.from_user.first_name
    menu_text = Dialog.MENU_TEXT.format(username=username)

    await callback.message.answer(
        text=menu_text,
        reply_markup=admin_menu_kb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=MenuStates.main_menu,
    )

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение меню пользователей: {e}")
