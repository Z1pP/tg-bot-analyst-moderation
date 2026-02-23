"""Тесты обработчика отчёта по чату (get_chat_report_handler, process_period_selection)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from constants import Dialog
from constants.callback import CallbackData
from handlers.private.reports.chat.chat_report_handler import (
    get_chat_report_handler,
    process_period_selection_callback,
)
from states import ChatStateManager


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
    st.get_data = AsyncMock(return_value={"chat_id": 1})
    st.set_state = AsyncMock()
    return st


@pytest.mark.asyncio
async def test_get_chat_report_handler_success_shows_period(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """Успешный сценарий: показ выбора периода и переход в selecting_period."""
    with patch(
        "handlers.private.reports.chat.chat_report_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        with patch(
            "handlers.private.reports.chat.chat_report_handler.time_period_ikb_chat",
            return_value=MagicMock(),
        ):
            await get_chat_report_handler(callback=callback, state=state)

    callback.answer.assert_called_once()
    mock_edit.assert_called_once()
    assert mock_edit.call_args.kwargs["text"] == Dialog.Report.SELECT_PERIOD
    state.set_state.assert_called_once_with(ChatStateManager.selecting_period)


@pytest.mark.asyncio
async def test_process_period_selection_no_chat_id_shows_error(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """При отсутствии chat_id в state показывается сообщение об ошибке."""
    callback.data = f"{CallbackData.Report.PREFIX_PERIOD}За сегодня"
    state.get_data = AsyncMock(return_value={})

    with patch(
        "handlers.private.reports.chat.chat_report_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        await process_period_selection_callback(
            callback=callback, state=state, container=MagicMock()
        )

    assert mock_edit.call_args.kwargs["text"] == Dialog.Chat.CHAT_NOT_SELECTED


@pytest.mark.asyncio
async def test_process_period_selection_success_calls_render(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """При выборе фиксированного периода вызывается _render_report_view."""
    callback.data = f"{CallbackData.Report.PREFIX_PERIOD}За сегодня"
    state.get_data = AsyncMock(return_value={"chat_id": 1})

    mock_result = MagicMock()
    mock_result.error_message = None
    mock_result.is_single_day = True
    mock_result.report_parts = ["Report text"]
    mock_usecase = MagicMock()
    mock_usecase.execute = AsyncMock(return_value=mock_result)
    container = MagicMock()
    container.resolve = MagicMock(return_value=mock_usecase)

    with patch(
        "handlers.private.reports.chat.chat_report_handler.safe_edit_message",
        new_callable=AsyncMock,
    ):
        with patch(
            "handlers.private.reports.chat.chat_report_handler._render_report_view",
            new_callable=AsyncMock,
        ) as mock_render:
            with patch(
                "handlers.private.reports.chat.chat_report_handler.chat_actions_ikb",
                return_value=MagicMock(),
            ):
                with patch(
                    "handlers.private.reports.chat.chat_report_handler.order_details_kb_chat",
                    return_value=MagicMock(),
                ):
                    await process_period_selection_callback(
                        callback=callback, state=state, container=container
                    )

    mock_render.assert_called_once()
    assert mock_render.call_args.kwargs["chat_id"] == 1
    assert mock_render.call_args.kwargs["period_text"] == "За сегодня"
