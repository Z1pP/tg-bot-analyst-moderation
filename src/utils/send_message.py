from aiogram.enums import ParseMode
from aiogram.types import Message


async def send_html_message(
    text: str,
    message: Message,
    parse_mode: ParseMode = ParseMode.HTML,
) -> None:
    await message.reply(text=text, parse_mode=parse_mode)
