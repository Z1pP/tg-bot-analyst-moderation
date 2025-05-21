from aiogram import F, Router
from aiogram.types import Message

from constants import KbCommands
from keyboards.reply.menu import get_moderators_list_kb
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.MENU)
async def menu_handler(message: Message) -> None:
    """
    Обработчик команды /menu и кнопки "Главное меню".
    Отображает главное меню бота.
    """
    user_name = message.from_user.first_name

    menu_text = (
        f"👋 Привет, <b>{user_name}</b>!\n\n"
        f"Это панель управления ботом для аналитики и модерации.\n"
        f"Выберите нужный раздел из меню ниже:"
    )

    await send_html_message_with_kb(
        message=message,
        text=menu_text,
        reply_markup=get_moderators_list_kb(),
    )
