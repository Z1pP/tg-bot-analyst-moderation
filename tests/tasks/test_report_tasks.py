"""Тесты report_tasks: send_chat_report_task."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from constants.period import TimePeriod
from tasks.report_tasks import send_chat_report_task


@pytest.fixture
def mock_schedule_service() -> MagicMock:
    svc = MagicMock()
    svc.get_schedule = AsyncMock()
    return svc


@pytest.fixture
def mock_send_reports_usecase() -> MagicMock:
    uc = MagicMock()
    uc.execute = AsyncMock()
    return uc


@pytest.mark.asyncio
async def test_send_chat_report_task_schedule_not_found_skips(
    mock_schedule_service: MagicMock,
) -> None:
    """send_chat_report_task пропускает выполнение когда расписание не найдено."""
    mock_schedule_service.get_schedule = AsyncMock(return_value=None)

    def resolve_fn(cls):
        from services.report_schedule_service import ReportScheduleService

        if cls is ReportScheduleService:
            return mock_schedule_service
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.report_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await send_chat_report_task(
            schedule_id=1,
            chat_id=1,
            period=TimePeriod.TODAY.value,
        )

    mock_schedule_service.get_schedule.assert_called_once_with(chat_id=1)


@pytest.mark.asyncio
async def test_send_chat_report_task_schedule_disabled_skips(
    mock_schedule_service: MagicMock,
    mock_send_reports_usecase: MagicMock,
) -> None:
    """send_chat_report_task пропускает выполнение когда рассылка отключена."""
    schedule = MagicMock()
    schedule.enabled = False
    mock_schedule_service.get_schedule = AsyncMock(return_value=schedule)

    def resolve_fn(cls):
        from services.report_schedule_service import ReportScheduleService
        from usecases.report.chat.send_daily_chat_reports import (
            SendDailyChatReportsUseCase,
        )

        if cls is ReportScheduleService:
            return mock_schedule_service
        if cls is SendDailyChatReportsUseCase:
            return mock_send_reports_usecase
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.report_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await send_chat_report_task(
            schedule_id=1,
            chat_id=1,
            period=TimePeriod.TODAY.value,
        )

    mock_send_reports_usecase.execute.assert_not_called()


@pytest.mark.asyncio
async def test_send_chat_report_task_success(
    mock_schedule_service: MagicMock,
    mock_send_reports_usecase: MagicMock,
) -> None:
    """send_chat_report_task вызывает usecase при включённом расписании."""
    schedule = MagicMock()
    schedule.enabled = True
    mock_schedule_service.get_schedule = AsyncMock(return_value=schedule)

    def resolve_fn(cls):
        from services.report_schedule_service import ReportScheduleService
        from usecases.report.chat.send_daily_chat_reports import (
            SendDailyChatReportsUseCase,
        )

        if cls is ReportScheduleService:
            return mock_schedule_service
        if cls is SendDailyChatReportsUseCase:
            return mock_send_reports_usecase
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.report_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await send_chat_report_task(
            schedule_id=1,
            chat_id=42,
            period=TimePeriod.YESTERDAY.value,
        )

    mock_send_reports_usecase.execute.assert_called_once_with(
        chat_id=42, period=TimePeriod.YESTERDAY.value
    )


@pytest.mark.asyncio
async def test_send_chat_report_task_get_schedule_exception_raises(
    mock_schedule_service: MagicMock,
) -> None:
    """send_chat_report_task пробрасывает исключение при ошибке get_schedule."""
    mock_schedule_service.get_schedule = AsyncMock(
        side_effect=RuntimeError("DB error")
    )

    def resolve_fn(cls):
        from services.report_schedule_service import ReportScheduleService

        if cls is ReportScheduleService:
            return mock_schedule_service
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.report_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        with pytest.raises(RuntimeError, match="DB error"):
            await send_chat_report_task(
                schedule_id=1,
                chat_id=1,
            )
