import logging

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import Dialog, KbCommands
from keyboards.reply.menu import admin_menu_kb, chat_menu_kb, user_menu_kb
from states import MenuStates
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


@router.message(F.text == KbCommands.USERS_MENU)
async def users_menu_handler(message: Message, state: FSMContext) -> None:
    await log_and_set_state(message, state, MenuStates.users_menu)

    await send_html_message_with_kb(
        message=message,
        text=Dialog.USER_MENU_TEXT,
        reply_markup=user_menu_kb(),
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

    await message.answer(f"Вкладка {KbCommands.SETTINGS} еще в разработке!")
