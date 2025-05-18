from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from constants import CommandList, Dialog
from utils.send_message import send_html_message

router = Router(name=__name__)


@router.message(Command(CommandList.START.name.lower()))
async def start_handler(message: Message) -> None:
    """
    Выводит приветственное сообщение
    """
    username = message.from_user.full_name
    welcome_text = Dialog.START_TEXT.format(username=username)

    await send_html_message(message=message, text=welcome_text)
