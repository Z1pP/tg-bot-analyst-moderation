"""Тесты для utils/send_message.py."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from utils.send_message import (
    safe_delete_message,
    safe_edit_message,
    safe_edit_message_reply_markup,
    sanitize_html_for_telegram,
    send_html_message_with_kb,
    send_split_html_message,
)


@pytest.mark.asyncio
async def test_send_html_message_with_kb() -> None:
    """send_html_message_with_kb вызывает message.reply с текстом и разметкой."""
    message = AsyncMock()
    message.reply = AsyncMock(return_value=message)
    kb = MagicMock()

    result = await send_html_message_with_kb(
        text="<b>Привет</b>",
        message=message,
        reply_markup=kb,
    )
    message.reply.assert_called_once_with(
        text="<b>Привет</b>",
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )
    assert result == message


@pytest.mark.asyncio
async def test_safe_delete_message_success() -> None:
    """safe_delete_message при успехе возвращает True (результат delete_message)."""
    bot = AsyncMock()
    bot.delete_message = AsyncMock(return_value=True)

    result = await safe_delete_message(bot, chat_id=1, message_id=2)
    assert result is True
    bot.delete_message.assert_called_once_with(chat_id=1, message_id=2)


@pytest.mark.asyncio
async def test_safe_delete_message_not_found_returns_false() -> None:
    """При 'message to delete not found' возвращается False."""
    bot = AsyncMock()
    bot.delete_message = AsyncMock(
        side_effect=TelegramBadRequest(
            message="message to delete not found",
            method="deleteMessage",
        )
    )
    result = await safe_delete_message(bot, chat_id=1, message_id=2)
    assert result is False


@pytest.mark.asyncio
async def test_safe_delete_message_forbidden_returns_false() -> None:
    """При TelegramForbiddenError возвращается False."""
    bot = AsyncMock()
    bot.delete_message = AsyncMock(
        side_effect=TelegramForbiddenError(message="Forbidden", method="deleteMessage")
    )
    result = await safe_delete_message(bot, chat_id=1, message_id=2)
    assert result is False


@pytest.mark.asyncio
async def test_safe_edit_message_success() -> None:
    """safe_edit_message при успехе возвращает результат edit_message_text."""
    bot = AsyncMock()
    edited = MagicMock()
    bot.edit_message_text = AsyncMock(return_value=edited)

    result = await safe_edit_message(bot, chat_id=1, message_id=2, text="Новый текст")
    assert result == edited
    bot.edit_message_text.assert_called_once()


@pytest.mark.asyncio
async def test_safe_edit_message_not_modified_returns_none() -> None:
    """При 'message is not modified' внутренний except возвращает None."""
    bot = AsyncMock()
    bot.edit_message_text = AsyncMock(
        side_effect=TelegramBadRequest(
            message="message is not modified",
            method="editMessageText",
        )
    )
    result = await safe_edit_message(bot, chat_id=1, message_id=2, text="Тот же текст")
    assert result is None


@pytest.mark.asyncio
async def test_safe_edit_message_reply_markup_success() -> None:
    """safe_edit_message_reply_markup при успехе возвращает True."""
    bot = AsyncMock()
    bot.edit_message_reply_markup = AsyncMock()
    result = await safe_edit_message_reply_markup(
        bot, chat_id=1, message_id=2, reply_markup=MagicMock()
    )
    assert result is True


def test_sanitize_html_for_telegram_empty() -> None:
    """Пустая строка возвращается как есть."""
    assert sanitize_html_for_telegram("") == ""


def test_sanitize_html_for_telegram_escapes_plain() -> None:
    """Обычный текст экранируется."""
    assert sanitize_html_for_telegram("<script>") == "&lt;script&gt;"
    assert "&lt;" in sanitize_html_for_telegram("a < b")


def test_sanitize_html_for_telegram_allowed_tags_preserved() -> None:
    """Разрешённые теги сохраняются."""
    text = "<b>жирный</b> и <i>курсив</i>"
    result = sanitize_html_for_telegram(text)
    assert "<b>" in result and "</b>" in result
    assert "<i>" in result and "</i>" in result


def test_sanitize_html_for_telegram_closes_unclosed_tags() -> None:
    """Незакрытые теги закрываются в конце."""
    result = sanitize_html_for_telegram("<b>только открытие")
    assert result.endswith("</b>")
    assert "<b>" in result


@pytest.mark.asyncio
async def test_send_split_html_message_empty_returns_empty_list() -> None:
    """Пустой текст даёт пустой список message_id."""
    bot = AsyncMock()
    result = await send_split_html_message(bot, chat_id=1, text="")
    assert result == []
    bot.send_message.assert_not_called()


@pytest.mark.asyncio
async def test_send_split_html_message_short_sends_one() -> None:
    """Короткий текст отправляется одним сообщением."""
    bot = AsyncMock()
    msg = MagicMock()
    msg.message_id = 42
    bot.send_message = AsyncMock(return_value=msg)

    result = await send_split_html_message(
        bot, chat_id=1, text="Короткий текст", limit=4096
    )
    assert result == [42]
    bot.send_message.assert_called_once()


@pytest.mark.asyncio
async def test_send_split_html_message_long_splits() -> None:
    """Длинный текст разбивается по лимиту и отправляется частями."""
    bot = AsyncMock()
    ids = [100, 101]
    call_count = 0

    async def send_mock(*args, **kwargs):
        nonlocal call_count
        m = MagicMock()
        m.message_id = ids[call_count]
        call_count += 1
        return m

    bot.send_message = AsyncMock(side_effect=send_mock)
    long_text = "a" * 5000
    result = await send_split_html_message(bot, chat_id=1, text=long_text, limit=2000)
    assert len(result) >= 2
    assert bot.send_message.call_count >= 2
