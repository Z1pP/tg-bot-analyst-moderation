from aiogram.enums import ParseMode
from aiogram.types import Message, ReplyMarkupUnion


async def send_html_message_with_kb(
    text: str,
    message: Message,
    parse_mode: ParseMode = ParseMode.HTML,
    reply_markup: ReplyMarkupUnion | None = None,
) -> None:
    await message.reply(
        text=text,
        parse_mode=parse_mode,
        reply_markup=reply_markup,
    )
