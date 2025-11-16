import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import Dialog, KbCommands
from keyboards.inline.users import users_menu_ikb
from keyboards.reply.menu import admin_menu_kb, chat_menu_kb
from states import MenuStates, UserStateManager
from utils.send_message import send_html_message_with_kb
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(F.text == KbCommands.MENU)
@router.message(Command("menu"))
@router.message(Command("start"))
async def menu_handler(message: Message, state: FSMContext) -> None:
    await log_and_set_state(message, state, MenuStates.main_menu)

    username = message.from_user.first_name
    menu_text = Dialog.MENU_TEXT.format(username=username)

    await send_html_message_with_kb(
        message=message,
        text=menu_text,
        reply_markup=admin_menu_kb(),
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата в главное меню через callback"""
    await callback.answer()
    await state.clear()

    username = callback.from_user.first_name
    menu_text = Dialog.MENU_TEXT.format(username=username)

    await callback.message.edit_text(
        text=menu_text,
        reply_markup=None,  # Убираем inline клавиатуру, показываем reply
    )

    await send_html_message_with_kb(
        message=callback.message,
        text=menu_text,
        reply_markup=admin_menu_kb(),
    )

    await log_and_set_state(callback.message, state, MenuStates.main_menu)


@router.message(F.text == KbCommands.USERS_MENU)
async def users_menu_handler(message: Message, state: FSMContext) -> None:
    """Обработчик меню пользователей через текстовую команду"""
    await state.clear()

    # Удаляем исходное сообщение
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")

    message_text = Dialog.User.SELECT_ACTION

    await message.answer(
        text=message_text,
        reply_markup=users_menu_ikb(),
    )

    await log_and_set_state(
        message=message,
        state=state,
        new_state=UserStateManager.users_menu,
    )


@router.message(F.text == KbCommands.CHATS_MENU)
async def chats_menu_handler(message: Message, state: FSMContext) -> None:
    await log_and_set_state(message, state, MenuStates.chats_menu)

    await send_html_message_with_kb(
        message=message,
        text=Dialog.CHATS_MENU_TEXT,
        reply_markup=chat_menu_kb(),
    )


@router.message(F.text == KbCommands.SETTINGS)
async def setting_handler(message: Message, state: FSMContext) -> None:
    await log_and_set_state(message, state, MenuStates.settings_menu)

    await message.answer(
        Dialog.Menu.SETTINGS_IN_DEVELOPMENT.format(settings=KbCommands.SETTINGS)
    )
