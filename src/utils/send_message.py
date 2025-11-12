import logging

from aiogram import Bot, types
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


async def send_html_message_with_kb(
    text: str,
    message: types.Message,
    parse_mode: ParseMode = ParseMode.HTML,
    reply_markup: types.ReplyMarkupUnion | None = None,
) -> None:
    await message.reply(
        text=text,
        parse_mode=parse_mode,
        reply_markup=reply_markup,
    )


async def safe_edit_message(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str | None = None,
    reply_markup: types.InlineKeyboardMarkup | None = None,
) -> bool:
    """Безопасное редактирование сообщения с обработкой типичных ошибок Telegram"""
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
        )
        return True

    except TelegramBadRequest as e:
        msg = (e.message or str(e)).lower()
        if "message is not modified" in msg:
            logger.debug("Сообщение %d не изменилось", message_id)
        elif "message to edit not found" in msg:
            logger.warning("Сообщение %d не найдено для редактирования", message_id)
        elif "message can't be edited" in msg:
            logger.warning("Сообщение %d больше нельзя редактировать", message_id)
        else:
            logger.error("Ошибка при редактировании сообщения: %s", e, exc_info=True)
        return False
