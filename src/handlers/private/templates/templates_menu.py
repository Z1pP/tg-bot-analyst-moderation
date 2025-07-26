from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from keyboards.reply.menu import tamplates_menu_kb
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(
    F.text == KbCommands.TEMPLATES_MENU,
)
async def templates_menu_handler(message: Message, state: FSMContext):
    """Обработчик меню шаблонов"""

    message_text = "Выбери действие:"

    await send_html_message_with_kb(
        message=message,
        text=message_text,
        reply_markup=tamplates_menu_kb(),
    )
