import html
import logging
import re
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
    parse_mode: str | None = ParseMode.HTML,
) -> types.Message | None:
    """Безопасное редактирование сообщения с обработкой типичных ошибок Telegram"""
    try:
        return await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            return None
        logger.error(f"Ошибка при редактировании сообщения с {parse_mode}: {e}")
        return await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
            parse_mode=None,
        )
    except Exception as e:
        logger.error(f"Критическая ошибка при редактировании сообщения: {e}")
        return None


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


def sanitize_html_for_telegram(text: str) -> str:
    """
    Экранирует текст для Telegram HTML, сохраняя разрешенные теги.
    Удаляет или экранирует все остальное.
    """
    if not text:
        return text

    # Список разрешенных тегов в Telegram
    allowed_tags = [
        "b",
        "strong",
        "i",
        "em",
        "u",
        "ins",
        "s",
        "strike",
        "del",
        "a",
        "code",
        "pre",
        "tg-spoiler",
        "span",
    ]

    # 1. Предварительная обработка: превращаем некоторые популярные теги в разрешенные
    # h1-h6 -> b
    text = re.sub(r"<(h[1-6])([^>]*)>", r"<b>", text, flags=re.IGNORECASE)
    text = re.sub(r"</(h[1-6])>", r"</b>", text, flags=re.IGNORECASE)
    # li -> •
    text = re.sub(r"<(li)([^>]*)>", r"• ", text, flags=re.IGNORECASE)
    text = re.sub(r"</(li)>", r"\n", text, flags=re.IGNORECASE)
    # p, div -> \n
    text = re.sub(r"<(p|div)([^>]*)>", r"", text, flags=re.IGNORECASE)
    text = re.sub(r"</(p|div)>", r"\n", text, flags=re.IGNORECASE)

    # 2. Основная санитария и балансировка тегов
    tag_re = re.compile(r"<(/?)(\w+)([^>]*)>")
    parts = []
    last_pos = 0
    stack = []

    for match in tag_re.finditer(text):
        # Текст перед тегом экранируем
        before = text[last_pos : match.start()]
        if before:
            parts.append(html.escape(html.unescape(before)))

        is_closing = bool(match.group(1))
        tag_name = match.group(2).lower()
        full_tag = match.group(0)

        if tag_name in allowed_tags:
            if is_closing:
                # Если это закрывающий тег, проверяем, есть ли он в стеке
                if tag_name in stack:
                    # Закрываем все теги до этого (включая этот)
                    while stack:
                        top = stack.pop()
                        parts.append(f"</{top}>")
                        if top == tag_name:
                            break
            else:
                # Если это открывающий тег, добавляем в стек и в результат
                stack.append(tag_name)
                parts.append(full_tag)
        else:
            # Экранируем неподдерживаемый тег
            parts.append(html.escape(full_tag))

        last_pos = match.end()

    after = text[last_pos:]
    if after:
        parts.append(html.escape(html.unescape(after)))

    # Закрываем все оставшиеся в стеке теги
    while stack:
        parts.append(f"</{stack.pop()}>")

    return "".join(parts)


async def send_split_html_message(
    bot: Bot,
    chat_id: int,
    text: str,
    limit: int = 4096,
) -> list[int]:
    """
    Разбивает длинный текст на части и отправляет их, соблюдая HTML-разметку в каждой части.
    """
    if not text:
        return []

    if len(text) <= limit:
        # Даже если текст короткий, прогоняем через санитизатор для балансировки тегов
        safe_text = sanitize_html_for_telegram(text)
        try:
            msg = await bot.send_message(
                chat_id=chat_id, text=safe_text, parse_mode=ParseMode.HTML
            )
            return [msg.message_id]
        except Exception as e:
            logger.error(f"Ошибка при отправке сообщения с HTML: {e}")
            msg = await bot.send_message(
                chat_id=chat_id, text=safe_text, parse_mode=None
            )
            return [msg.message_id]

    message_ids = []
    # Работаем с исходным текстом, разбивая его на части
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

        # Санитизируем и балансируем теги ОТДЕЛЬНО для каждого куска
        safe_chunk = sanitize_html_for_telegram(chunk)

        try:
            msg = await bot.send_message(
                chat_id=chat_id, text=safe_chunk, parse_mode=ParseMode.HTML
            )
            message_ids.append(msg.message_id)
        except Exception as e:
            logger.error(f"Ошибка при отправке части сообщения с HTML: {e}")
            try:
                msg = await bot.send_message(
                    chat_id=chat_id, text=safe_chunk, parse_mode=None
                )
                message_ids.append(msg.message_id)
            except Exception as e2:
                logger.error(f"Критическая ошибка при отправке части сообщения: {e2}")

    return message_ids
