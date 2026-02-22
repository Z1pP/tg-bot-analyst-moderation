"""Тесты обработчика возврата к выбору периода отчёта (reports/chat)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from constants import Dialog
from handlers.private.reports.chat.back_to_periods_handler import (
    back_to_periods_handler,
)


@pytest.fixture
def callback() -> MagicMock:
    """Мок CallbackQuery."""
    cb = MagicMock()
    cb.answer = AsyncMock()
    cb.from_user = MagicMock()
    cb.from_user.id = 12345
    cb.message = MagicMock()
    cb.message.chat = MagicMock()
    cb.message.chat.id = 100
    cb.message.message_id = 1
    cb.bot = MagicMock()
    return cb


@pytest.fixture
def state() -> MagicMock:
    """Мок FSMContext."""
    st = MagicMock()
    st.get_state = AsyncMock(return_value="ChatStateManager:selecting_custom_period")
    st.set_state = AsyncMock()
    return st


@pytest.mark.asyncio
async def test_back_to_periods_handler_calls_answer_and_edit(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """Обработчик вызывает callback.answer(), safe_edit_message с текстом периода, state.set_state."""
    with patch(
        "handlers.private.reports.chat.back_to_periods_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        with patch(
            "handlers.private.reports.chat.back_to_periods_handler.time_period_ikb_chat",
            return_value=MagicMock(),
        ):
            await back_to_periods_handler(callback=callback, state=state)

    callback.answer.assert_called_once()
    mock_edit.assert_called_once()
    call_kw = mock_edit.call_args.kwargs
    assert call_kw["text"] == Dialog.Report.SELECT_PERIOD
    assert call_kw["chat_id"] == 100
    assert call_kw["message_id"] == 1
    state.set_state.assert_called_once()


@pytest.mark.asyncio
async def test_back_to_periods_handler_rating_state_uses_rating_text(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """В состоянии рейтинга выводится текст выбора периода рейтинга."""
    state.get_state = AsyncMock(
        return_value="RatingStateManager:selecting_custom_period"
    )

    with patch(
        "handlers.private.reports.chat.back_to_periods_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        with patch(
            "handlers.private.reports.chat.back_to_periods_handler.time_period_ikb_chat",
            return_value=MagicMock(),
        ):
            await back_to_periods_handler(callback=callback, state=state)

    call_kw = mock_edit.call_args.kwargs
    assert call_kw["text"] == Dialog.Rating.SELECT_PERIOD
