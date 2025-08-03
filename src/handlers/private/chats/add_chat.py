from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from constants import KbCommands
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.message(F.text == KbCommands.ADD_CHAT)
async def add_chat_handler(message: Message, state: FSMContext) -> None:
    """
    Хендлер для команды добавления чата.
    """

    message_text = (
        "📨 <b>Добавление чата в отслеживание</b>\n\n"
        "📋 <b>Инструкция:</b>\n"
        "1️⃣ Добавьте бота в нужный чат\n"
        "2️⃣ Дайте боту права администратора\n"
        "3️⃣ Напишите команду <code>/track</code> в чате\n\n"
        "✅ Если все успешно, вы получите уведомление здесь об успешном добавлении чата"
    )

    await send_html_message_with_kb(
        message=message,
        text=message_text,
    )
