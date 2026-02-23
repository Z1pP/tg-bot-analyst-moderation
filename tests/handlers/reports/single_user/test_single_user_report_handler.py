"""Тесты обработчиков отчёта по одному пользователю (single_user_report_handler)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from constants import Dialog
from constants.callback import CallbackData
from handlers.private.reports.single_user.single_user_report_handler import (
    get_user_report_handler,
    process_period_selection_callback,
)
from states import SingleUserReportStates


@pytest.fixture
def callback() -> MagicMock:
    """Мок CallbackQuery."""
    cb = MagicMock()
    cb.answer = AsyncMock()
    cb.from_user = MagicMock()
    cb.from_user.id = 12345
    cb.from_user.username = "admin"
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
    st.get_data = AsyncMock(return_value={"user_id": 777})
    st.set_state = AsyncMock()
    return st


@pytest.mark.asyncio
async def test_get_user_report_handler_no_user_id_shows_error(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """При отсутствии user_id в state показывается сообщение об ошибке."""
    state.get_data = AsyncMock(return_value={})

    with patch(
        "handlers.private.reports.single_user.single_user_report_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        with patch(
            "handlers.private.reports.single_user.single_user_report_handler.user_actions_ikb",
            return_value=MagicMock(),
        ):
            await get_user_report_handler(
                callback=callback, state=state, container=MagicMock()
            )

    mock_edit.assert_called_once()
    assert mock_edit.call_args.kwargs["text"] == Dialog.Report.ERROR_SELECT_USER_AGAIN


@pytest.mark.asyncio
async def test_get_user_report_handler_no_tracked_chats_shows_instructions(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """При отсутствии отслеживаемых чатов показывается инструкция."""
    mock_tracked = MagicMock()
    mock_tracked.chats = []
    mock_usecase = MagicMock()
    mock_usecase.execute = AsyncMock(return_value=mock_tracked)
    container = MagicMock()
    container.resolve = MagicMock(return_value=mock_usecase)

    with patch(
        "handlers.private.reports.single_user.single_user_report_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        with patch(
            "handlers.private.reports.single_user.single_user_report_handler.user_actions_ikb",
            return_value=MagicMock(),
        ):
            with patch(
                "handlers.private.reports.single_user.single_user_report_handler.time_period_ikb_single_user",
                return_value=MagicMock(),
            ):
                await get_user_report_handler(
                    callback=callback, state=state, container=container
                )

    mock_usecase.execute.assert_called_once_with(tg_id="12345")
    assert (
        mock_edit.call_args.kwargs["text"]
        == Dialog.Report.NO_TRACKED_CHATS_WITH_INSTRUCTIONS
    )


@pytest.mark.asyncio
async def test_get_user_report_handler_success_shows_period_select(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """Успешный сценарий: есть чаты — показ выбора периода и переход в selecting_period."""
    mock_tracked = MagicMock()
    mock_tracked.chats = [MagicMock()]
    mock_usecase = MagicMock()
    mock_usecase.execute = AsyncMock(return_value=mock_tracked)
    container = MagicMock()
    container.resolve = MagicMock(return_value=mock_usecase)

    with patch(
        "handlers.private.reports.single_user.single_user_report_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        with patch(
            "handlers.private.reports.single_user.single_user_report_handler.time_period_ikb_single_user",
            return_value=MagicMock(),
        ):
            await get_user_report_handler(
                callback=callback, state=state, container=container
            )

    mock_edit.assert_called_once()
    assert mock_edit.call_args.kwargs["text"] == Dialog.Report.SELECT_PERIOD
    state.set_state.assert_called_once_with(SingleUserReportStates.selecting_period)


@pytest.mark.asyncio
async def test_process_period_selection_custom_shows_calendar(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """Выбор периода «За другой период» — показ календаря и переход в selecting_custom_period."""
    callback.data = f"{CallbackData.Report.PREFIX_PERIOD}За другой период"
    state.get_data = AsyncMock(return_value={"user_id": 777})
    state.set_state = AsyncMock()
    state.update_data = AsyncMock()

    mock_now = MagicMock()
    mock_now.year = 2025
    mock_now.month = 2
    mock_get_now = MagicMock()
    mock_get_now.execute = MagicMock(return_value=mock_now)
    container = MagicMock()
    container.resolve = MagicMock(return_value=mock_get_now)

    with patch(
        "handlers.private.reports.single_user.single_user_report_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        with patch(
            "handlers.private.reports.single_user.single_user_report_handler.CalendarKeyboard",
        ) as mock_cal:
            mock_cal.create_calendar_single_user.return_value = MagicMock()
            await process_period_selection_callback(
                callback=callback, state=state, container=container
            )

    state.set_state.assert_called_once_with(
        SingleUserReportStates.selecting_custom_period
    )
    mock_edit.assert_called_once()
    assert (
        "дату" in mock_edit.call_args.kwargs["text"].lower()
        or "дата" in mock_edit.call_args.kwargs["text"].lower()
    )


@pytest.mark.asyncio
async def test_process_period_selection_fixed_period_calls_render(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """Выбор фиксированного периода (например «За сегодня») — вызов _render_report_view."""
    callback.data = f"{CallbackData.Report.PREFIX_PERIOD}За сегодня"
    state.get_data = AsyncMock(return_value={"user_id": 777})

    mock_result = MagicMock()
    mock_result.error_message = None
    mock_result.is_single_day = True
    mock_result.report_parts = ["Part1"]
    mock_usecase = MagicMock()
    mock_usecase.execute = AsyncMock(return_value=mock_result)
    container = MagicMock()
    container.resolve = MagicMock(return_value=mock_usecase)

    with patch(
        "handlers.private.reports.single_user.single_user_report_handler.safe_edit_message",
        new_callable=AsyncMock,
    ):
        with patch(
            "handlers.private.reports.single_user.single_user_report_handler._render_report_view",
            new_callable=AsyncMock,
        ) as mock_render:
            with patch(
                "handlers.private.reports.single_user.single_user_report_handler.user_actions_ikb",
                return_value=MagicMock(),
            ):
                with patch(
                    "handlers.private.reports.single_user.single_user_report_handler.order_details_kb_single_user",
                    return_value=MagicMock(),
                ):
                    await process_period_selection_callback(
                        callback=callback, state=state, container=container
                    )

    mock_render.assert_called_once()
    call_kw = mock_render.call_args.kwargs
    assert call_kw["user_id"] == 777
    assert call_kw["selected_period"] == "За сегодня"
