from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from keyboards.inline.chats import chats_management_ikb
from keyboards.inline.menu import admin_menu_ikb
from states import MenuStates
from utils.send_message import safe_edit_message


async def show_main_menu(
    callback: CallbackQuery, state: FSMContext, user_language: str
) -> None:
    """Helper to show the main menu and clear state."""
    await state.clear()

    username = callback.from_user.first_name
    menu_text = Dialog.Menu.MENU_TEXT.format(username=username)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=menu_text,
        reply_markup=admin_menu_ikb(
            user_language=user_language,
            admin_tg_id=str(callback.from_user.id),
        ),
    )
    await state.set_state(MenuStates.main_menu)


async def show_chats_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Helper to show the chats management menu and clear state."""
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.CHAT_MANAGEMENT,
        reply_markup=chats_management_ikb(),
    )
    await state.set_state(MenuStates.chats_menu)
