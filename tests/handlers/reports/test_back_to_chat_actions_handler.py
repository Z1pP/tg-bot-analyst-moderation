"""Тесты обработчика возврата к действиям чата (back_to_chat_actions)."""

from datetime import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from constants import Dialog
from handlers.private.reports.chat.back_to_chat_actions_handler import (
    back_to_chat_actions_handler,
)


@pytest.fixture
def callback() -> MagicMock:
    """Мок CallbackQuery."""
    cb = MagicMock()
    cb.answer = AsyncMock()
    cb.message = MagicMock()
    cb.message.chat = MagicMock()
    cb.message.chat.id = 100
    cb.message.message_id = 1
    cb.bot = MagicMock()
    return cb


@pytest.fixture
def state() -> MagicMock:
    """Мок FSMContext с get_value для chat_id."""
    st = MagicMock()
    st.get_value = AsyncMock(return_value=1)
    st.set_state = AsyncMock()
    return st


@pytest.fixture
def sample_chat() -> MagicMock:
    """Чат с title и временами для форматирования."""
    chat = MagicMock()
    chat.id = 1
    chat.title = "Test Chat"
    chat.start_time = time(9, 0)
    chat.end_time = time(18, 0)
    return chat


@pytest.mark.asyncio
async def test_back_to_chat_actions_no_chat_id_shows_error(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """При отсутствии chat_id в state показывается сообщение об ошибке."""
    state.get_value = AsyncMock(return_value=None)
    with patch(
        "handlers.private.reports.chat.back_to_chat_actions_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        with patch(
            "handlers.private.reports.chat.back_to_chat_actions_handler.chat_actions_ikb",
            return_value=MagicMock(),
        ):
            await back_to_chat_actions_handler(
                callback=callback, state=state, container=MagicMock()
            )

    mock_edit.assert_called_once()
    assert (
        mock_edit.call_args.kwargs["text"]
        == Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED
    )


@pytest.mark.asyncio
async def test_back_to_chat_actions_success_edits_message(
    callback: MagicMock,
    state: MagicMock,
    sample_chat: MagicMock,
) -> None:
    """Успешный сценарий: resolve use case, execute возвращает чат — вызывается safe_edit_message с текстом действий."""
    mock_usecase = MagicMock()
    mock_usecase.execute = AsyncMock(return_value=sample_chat)
    container = MagicMock()
    container.resolve = MagicMock(return_value=mock_usecase)

    with patch(
        "handlers.private.reports.chat.back_to_chat_actions_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        with patch(
            "handlers.private.reports.chat.back_to_chat_actions_handler.chat_actions_ikb",
            return_value=MagicMock(),
        ):
            await back_to_chat_actions_handler(
                callback=callback, state=state, container=container
            )

    callback.answer.assert_called_once()
    mock_usecase.execute.assert_called_once()
    mock_edit.assert_called_once()
    text = mock_edit.call_args.kwargs["text"]
    # Текст меню действий чата (CHAT_ACTIONS_INFO) без плейсхолдеров title/start_time в константе
    assert "Время сбора данных" in text or "Архивный чат" in text
    state.set_state.assert_called_once()
