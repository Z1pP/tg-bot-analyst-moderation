"""Тесты обработчика календаря отчётов (calendar_handler)."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from constants.callback import CallbackData
from handlers.private.reports.calendar_handler import (
    _create_calendar_by_state,
    calendar_handler,
    handle_navigation,
    handle_reset,
)
from states import (
    ChatStateManager,
    SingleUserReportStates,
)


@pytest.fixture
def callback() -> MagicMock:
    """Мок CallbackQuery."""
    cb = MagicMock()
    cb.answer = AsyncMock()
    cb.data = f"{CallbackData.Report.PREFIX_CALENDAR}ignore_0_0"
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
    st.get_data = AsyncMock(return_value={"cal_start_date": None, "cal_end_date": None})
    st.get_state = AsyncMock(
        return_value=SingleUserReportStates.selecting_custom_period.state
    )
    return st


@pytest.mark.asyncio
async def test_calendar_handler_action_ignore_returns_early(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """Действие 'ignore' — ответ на callback без изменения сообщения."""
    callback.data = f"{CallbackData.Report.PREFIX_CALENDAR}ignore_0_0"

    with patch(
        "handlers.private.reports.calendar_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        await calendar_handler(callback=callback, state=state, container=MagicMock())

    callback.answer.assert_called_once()
    mock_edit.assert_not_called()


@pytest.mark.asyncio
async def test_calendar_handler_action_prev_calls_handle_navigation(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """Действие 'prev' — вызов handle_navigation и обновление сообщения."""
    callback.data = f"{CallbackData.Report.PREFIX_CALENDAR}prev_2025_2"
    state.get_data = AsyncMock(
        return_value={"cal_start_date": None, "cal_end_date": None}
    )
    state.get_state = AsyncMock(
        return_value=SingleUserReportStates.selecting_custom_period.state
    )

    with patch(
        "handlers.private.reports.calendar_handler.safe_edit_message",
        new_callable=AsyncMock,
    ):
        with patch(
            "handlers.private.reports.calendar_handler.handle_navigation",
            new_callable=AsyncMock,
        ) as mock_nav:
            await calendar_handler(
                callback=callback, state=state, container=MagicMock()
            )

    mock_nav.assert_called_once()
    call_kw = mock_nav.call_args.kwargs
    assert call_kw["action"] == "prev"
    assert call_kw["year"] == 2025
    assert call_kw["month"] == 2


@pytest.mark.asyncio
async def test_handle_navigation_prev_decrements_month(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """Навигация prev — уменьшение месяца и вызов safe_edit_message."""
    state.get_state = AsyncMock(
        return_value=SingleUserReportStates.selecting_custom_period.state
    )

    with patch(
        "handlers.private.reports.calendar_handler._create_calendar_by_state",
        return_value=MagicMock(),
    ) as mock_create:
        with patch(
            "handlers.private.reports.calendar_handler.safe_edit_message",
            new_callable=AsyncMock,
        ) as mock_edit:
            await handle_navigation(
                callback=callback,
                state=state,
                action="prev",
                year=2025,
                month=2,
                cal_start=None,
                cal_end=None,
            )

    mock_create.assert_called_once()
    assert mock_create.call_args.kwargs["year"] == 2025
    assert mock_create.call_args.kwargs["month"] == 1
    mock_edit.assert_called_once()


@pytest.mark.asyncio
async def test_handle_reset_single_user_state(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """Сброс календаря в состоянии single_user — календарь single_user и SELECT_START_DATE."""
    state.get_state = AsyncMock(
        return_value=SingleUserReportStates.selecting_custom_period.state
    )
    state.update_data = AsyncMock()

    mock_now = MagicMock()
    mock_now.year = 2025
    mock_now.month = 2
    mock_get_now = MagicMock()
    mock_get_now.execute = MagicMock(return_value=mock_now)
    container = MagicMock()
    container.resolve = MagicMock(return_value=mock_get_now)

    with patch(
        "handlers.private.reports.calendar_handler.CalendarKeyboard",
    ) as mock_kb:
        mock_kb.create_calendar_single_user.return_value = MagicMock()
        with patch(
            "handlers.private.reports.calendar_handler.safe_edit_message",
            new_callable=AsyncMock,
        ) as mock_edit:
            await handle_reset(callback=callback, state=state, container=container)

    mock_kb.create_calendar_single_user.assert_called_once_with(year=2025, month=2)
    mock_edit.assert_called_once()


def test_create_calendar_by_state_single_user_returns_keyboard() -> None:
    """_create_calendar_by_state для SingleUserReportStates возвращает клавиатуру."""
    with patch(
        "handlers.private.reports.calendar_handler.CalendarKeyboard",
    ) as mock_kb:
        mock_kb.create_calendar_single_user.return_value = MagicMock()
        result = _create_calendar_by_state(
            current_state=SingleUserReportStates.selecting_custom_period.state,
            year=2025,
            month=2,
            start_date=datetime(2025, 2, 1),
            end_date=None,
        )
    assert result is not None
    mock_kb.create_calendar_single_user.assert_called_once()


def test_create_calendar_by_state_chat_returns_keyboard() -> None:
    """_create_calendar_by_state для ChatStateManager возвращает клавиатуру чата."""
    with patch(
        "handlers.private.reports.calendar_handler.CalendarKeyboard",
    ) as mock_kb:
        mock_kb.create_calendar_chat.return_value = MagicMock()
        result = _create_calendar_by_state(
            current_state=ChatStateManager.selecting_custom_period.state,
            year=2025,
            month=2,
            start_date=datetime(2025, 2, 1),
            end_date=None,
        )
    assert result is not None
    mock_kb.create_calendar_chat.assert_called_once()


def test_create_calendar_by_state_unknown_returns_none() -> None:
    """Неизвестное состояние — возврат None."""
    result = _create_calendar_by_state(
        current_state="UnknownState:foo",
        year=2025,
        month=2,
        start_date=datetime(2025, 2, 1),
        end_date=None,
    )
    assert result is None
