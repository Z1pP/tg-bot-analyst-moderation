from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from keyboards.reply.menu import admin_menu_kb
from keyboards.reply.user_actions import get_user_actions_kb
from states.user_states import UserStateManager
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.MENU)
@router.message(Command("menu"))
@router.message(Command("start"))
async def menu_handler(message: Message, state: FSMContext) -> None:
    """
    Обработчик команды /menu, /start и кнопки "Главное меню".
    Отображает главное меню бота.
    """
    # Очищаем состояние FSM
    await state.clear()

    user_name = message.from_user.first_name

    menu_text = (
        f"👋 Привет, <b>{user_name}</b>!\n\n"
        f"Это панель управления ботом для аналитики и модерации.\n"
        f"Выберите нужный раздел из меню ниже:"
    )

    await send_html_message_with_kb(
        message=message,
        text=menu_text,
        reply_markup=admin_menu_kb(),
    )
