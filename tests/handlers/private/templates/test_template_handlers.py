"""Тесты хендлеров шаблонов: импорт роутера и защитные ветки."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import types

from handlers.private.templates import router as templates_router
from handlers.private.templates.delete_template import (
    confirmation_removing_template_handler,
)
from handlers.private.templates.list_templates import templates_list_handler
from handlers.private.templates.select_template import hide_template_handler


def _callback(data: str) -> MagicMock:
    callback = MagicMock()
    callback.data = data
    callback.from_user.id = 42
    callback.from_user.username = "admin"
    callback.from_user.full_name = "Admin"
    callback.answer = AsyncMock()
    callback.bot = AsyncMock()
    callback.message = MagicMock()
    callback.message.__class__ = types.Message
    callback.message.chat.id = 10
    callback.message.message_id = 20
    return callback


def test_templates_router_imports() -> None:
    """Модуль шаблонов импортируется целиком (ловит битые импорты клавиатур)."""
    assert templates_router.name == "templates_router"


@pytest.mark.asyncio
async def test_templates_list_handler_shows_error_via_callback() -> None:
    """При ошибке пользователю редактируется сообщение, а не падает хендлер."""
    callback = _callback("select_template")
    state = AsyncMock()
    container = MagicMock()
    container.resolve.side_effect = RuntimeError("boom")

    await templates_list_handler(callback=callback, state=state, container=container)

    callback.bot.edit_message_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_without_template_id_does_not_call_usecase() -> None:
    """Без template_id в state удаление не запускается."""
    callback = _callback("conf_remove_template__yes")
    state = AsyncMock()
    state.get_data.return_value = {}
    container = MagicMock()

    await confirmation_removing_template_handler(
        callback=callback, state=state, container=container
    )

    container.resolve.assert_not_called()
    callback.bot.edit_message_text.assert_awaited_once()


@pytest.mark.asyncio
async def test_hide_template_without_message_does_nothing() -> None:
    """Без доступного сообщения скрытие шаблона не трогает Telegram."""
    callback = _callback("hide_template_5")
    callback.message = None

    await hide_template_handler(callback=callback)

    callback.bot.delete_message.assert_not_called()