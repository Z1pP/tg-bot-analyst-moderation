from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from constants import CommandList, Dialog
from constants.work_time import WORK_END, WORK_START
from utils.send_message import send_html_message

router = Router(name=__name__)


@router.message(Command(CommandList.HELP.name.lower()))
async def help_handler(message: Message) -> None:
    """
    Выводит инструкцию по использованию бота
    """
    help_text = Dialog.HELP_TEXT.format(
        WORK_START=WORK_START.strftime("%H.%M"),
        WORK_END=WORK_END.strftime("%H.%M"),
        TOLERANCE="10",
    )

    await send_html_message(message=message, text=help_text)
