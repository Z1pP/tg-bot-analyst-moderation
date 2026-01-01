import logging
from functools import wraps

from aiogram import Bot, types
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)


def safe_telegram_edit(func):
    """Декоратор для безопасного редактирования сообщений Telegram"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Пытаемся получить message_id для логов
        message_id = kwargs.get("message_id")
        if not message_id and len(args) > 2:
            message_id = args[2]

        try:
            return await func(*args, **kwargs)
        except TelegramBadRequest as e:
            msg = (e.message or str(e)).lower()
            if "message is not modified" in msg:
                logger.debug("Сообщение %s не изменилось", message_id)
            elif "message to edit not found" in msg:
                logger.warning("Сообщение %s не найдено для редактирования", message_id)
            elif "message can't be edited" in msg:
                logger.warning("Сообщение %s больше нельзя редактировать", message_id)
            else:
                logger.error(
                    "Ошибка при выполнении %s: %s", func.__name__, e, exc_info=True
                )
            return False

    return wrapper


async def send_html_message_with_kb(
    text: str,
    message: types.Message,
    parse_mode: ParseMode = ParseMode.HTML,
    reply_markup: types.ReplyMarkupUnion | None = None,
) -> types.Message:
    """Отправляет HTML сообщение с клавиатурой и возвращает объект сообщения."""
    return await message.reply(
        text=text,
        parse_mode=parse_mode,
        reply_markup=reply_markup,
    )


@safe_telegram_edit
async def safe_edit_message(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str | None = None,
    reply_markup: types.InlineKeyboardMarkup | None = None,
) -> bool:
    """Безопасное редактирование сообщения с обработкой типичных ошибок Telegram"""
    await bot.edit_message_text(
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=reply_markup,
    )
    return True


@safe_telegram_edit
async def safe_edit_message_reply_markup(
    bot: Bot,
    chat_id: int,
    message_id: int,
    reply_markup: types.InlineKeyboardMarkup | None = None,
) -> bool:
    """Безопасное редактирование только клавиатуры сообщения с обработкой типичных ошибок Telegram"""
    await bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=reply_markup,
    )
    return True


async def send_split_html_message(
    bot: Bot,
    chat_id: int,
    text: str,
    limit: int = 4096,
) -> list[int]:
    """
    Разбивает длинный HTML текст на части и отправляет их.
    Старается разбивать по переходам строк.
    Возвращает список ID отправленных сообщений.
    """
    if len(text) <= limit:
        msg = await bot.send_message(
            chat_id=chat_id, text=text, parse_mode=ParseMode.HTML
        )
        return [msg.message_id]

    message_ids = []
    while text:
        if len(text) <= limit:
            chunk = text
            text = ""
        else:
            # Ищем последний перенос строки в пределах лимита
            chunk = text[:limit]
            last_newline = chunk.rfind("\n")
            if last_newline != -1 and last_newline > limit // 2:
                chunk = text[:last_newline]
                text = text[last_newline + 1 :]
            else:
                text = text[limit:]

        try:
            msg = await bot.send_message(
                chat_id=chat_id, text=chunk, parse_mode=ParseMode.HTML
            )
            message_ids.append(msg.message_id)
        except Exception as e:
            logger.error(f"Ошибка при отправке части сообщения: {e}")
            # Пытаемся отправить без HTML, если ошибка в тегах
            try:
                msg = await bot.send_message(chat_id=chat_id, text=chunk)
                message_ids.append(msg.message_id)
            except Exception as e2:
                logger.error(f"Критическая ошибка при отправке части сообщения: {e2}")

    return message_ids
