"""Тесты обработчика отчёта по всем пользователям (all_users_report_handler)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from constants import Dialog
from constants.callback import CallbackData
from handlers.private.reports.all_users.all_users_report_handler import (
    get_all_users_report_handler,
    process_period_selection_callback,
)
from states import AllUsersReportStates


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
    st.get_data = AsyncMock(return_value={})
    st.set_state = AsyncMock()
    st.update_data = AsyncMock()
    return st


@pytest.mark.asyncio
async def test_get_all_users_report_handler_no_chats_shows_instructions(
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
        "handlers.private.reports.all_users.all_users_report_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        with patch(
            "handlers.private.reports.all_users.all_users_report_handler.all_users_actions_ikb",
            return_value=MagicMock(),
        ):
            await get_all_users_report_handler(
                callback=callback, state=state, container=container
            )

    assert (
        mock_edit.call_args.kwargs["text"]
        == Dialog.Report.NO_TRACKED_CHATS_WITH_INSTRUCTIONS
    )


@pytest.mark.asyncio
async def test_get_all_users_report_handler_success_shows_period(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """Успешный сценарий: показ выбора периода и переход в selecting_period."""
    mock_tracked = MagicMock()
    mock_tracked.chats = [MagicMock()]
    mock_usecase = MagicMock()
    mock_usecase.execute = AsyncMock(return_value=mock_tracked)
    container = MagicMock()
    container.resolve = MagicMock(return_value=mock_usecase)

    with patch(
        "handlers.private.reports.all_users.all_users_report_handler.safe_edit_message",
        new_callable=AsyncMock,
    ) as mock_edit:
        with patch(
            "handlers.private.reports.all_users.all_users_report_handler.time_period_ikb_all_users",
            return_value=MagicMock(),
        ):
            await get_all_users_report_handler(
                callback=callback, state=state, container=container
            )

    mock_edit.assert_called_once()
    assert (
        Dialog.Report.SELECT_PERIOD_COLON in mock_edit.call_args.kwargs["text"]
        or "Период" in mock_edit.call_args.kwargs["text"]
    )
    state.set_state.assert_called_once_with(AllUsersReportStates.selecting_period)


@pytest.mark.asyncio
async def test_process_period_selection_all_users_calls_render(
    callback: MagicMock,
    state: MagicMock,
) -> None:
    """Выбор периода «За сегодня» вызывает _render_all_users_report."""
    callback.data = f"{CallbackData.Report.PREFIX_PERIOD}За сегодня"

    mock_result = MagicMock()
    mock_result.error_message = None
    mock_result.is_single_day = True
    mock_result.report_parts = ["Report"]
    mock_usecase = MagicMock()
    mock_usecase.execute = AsyncMock(return_value=mock_result)
    container = MagicMock()
    container.resolve = MagicMock(return_value=mock_usecase)

    with patch(
        "handlers.private.reports.all_users.all_users_report_handler.safe_edit_message",
        new_callable=AsyncMock,
    ):
        with patch(
            "handlers.private.reports.all_users.all_users_report_handler._render_all_users_report",
            new_callable=AsyncMock,
        ) as mock_render:
            with patch(
                "handlers.private.reports.all_users.all_users_report_handler.all_users_actions_ikb",
                return_value=MagicMock(),
            ):
                with patch(
                    "handlers.private.reports.all_users.all_users_report_handler.order_details_kb_all_users",
                    return_value=MagicMock(),
                ):
                    await process_period_selection_callback(
                        callback=callback, state=state, container=container
                    )

    mock_render.assert_called_once()
    assert mock_render.call_args.kwargs["selected_period"] == "За сегодня"
