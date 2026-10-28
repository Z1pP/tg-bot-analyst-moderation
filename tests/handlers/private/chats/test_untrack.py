"""Тесты подтверждения удаления чата из отслеживания."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import types

from constants import Dialog
from constants.callback import CallbackData
from handlers.private.chats import untrack
from usecases.chat_tracking import RemoveChatFromTrackingUseCase


def _callback(answer: str = "yes") -> MagicMock:
    callback = MagicMock()
    callback.data = f"{CallbackData.Chat.PREFIX_CONFIRM_REMOVE_CHAT}{answer}"
    callback.from_user.id = 42
    callback.from_user.username = "admin"
    callback.answer = AsyncMock()
    callback.bot = AsyncMock()
    callback.message = MagicMock()
    callback.message.__class__ = types.Message
    callback.message.chat.id = 10
    callback.message.message_id = 20
    return callback


def _container(result: MagicMock) -> MagicMock:
    remove_chat = AsyncMock()
    remove_chat.execute.return_value = result

    def resolve(cls: type) -> AsyncMock:
        return {RemoveChatFromTrackingUseCase: remove_chat}[cls]

    container = MagicMock()
    container.resolve.side_effect = resolve
    return container


@pytest.mark.asyncio
async def test_confirm_untrack_calls_usecase_with_chat_id() -> None:
    """Удаление вызывает use case с DB id чата из состояния."""
    result = MagicMock(success=True)
    container = _container(result)
    state = AsyncMock()
    state.get_data.return_value = {"chat_id": 7}

    await untrack.confirmation_untracking_chat_handler(
        callback=_callback("yes"), state=state, container=container
    )

    remove_chat = container.resolve(RemoveChatFromTrackingUseCase)
    remove_chat.execute.assert_awaited_once_with(
        admin_tg_id="42",
        admin_username="admin",
        chat_id=7,
    )


@pytest.mark.asyncio
async def test_confirm_untrack_shows_success_message() -> None:
    """При успехе пользователь видит сообщение об удалении чата."""
    container = _container(MagicMock(success=True))
    state = AsyncMock()
    state.get_data.return_value = {"chat_id": 7}
    callback = _callback("yes")

    await untrack.confirmation_untracking_chat_handler(
        callback=callback, state=state, container=container
    )

    callback.bot.edit_message_text.assert_awaited_once()
    assert (
        callback.bot.edit_message_text.call_args.kwargs["text"]
        == Dialog.Chat.CHAT_REMOVED
    )


@pytest.mark.asyncio
async def test_confirm_untrack_without_chat_id_shows_error() -> None:
    """Если chat_id потерян, use case удаления не вызывается."""
    container = _container(MagicMock(success=False))
    state = AsyncMock()
    state.get_data.return_value = {}

    await untrack.confirmation_untracking_chat_handler(
        callback=_callback("yes"), state=state, container=container
    )

    remove_chat = container.resolve(RemoveChatFromTrackingUseCase)
    remove_chat.execute.assert_not_called()