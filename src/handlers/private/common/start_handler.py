from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from punq import Container

from constants import Dialog
from keyboards.inline.menu import main_menu_ikb

router = Router(name=__name__)


@router.message(CommandStart())
async def start_handler(
    message: Message, container: Container, user_language: str
) -> None:
    """
    Выводит приветственное сообщение
    """
    username = message.from_user.full_name
    welcome_text = Dialog.Menu.MENU_TEXT.format(username=username)

    await message.answer(
        text=welcome_text,
        reply_markup=main_menu_ikb(
            user=None,
            user_language=user_language,
            admin_tg_id=str(message.from_user.id),
        ),
    )
