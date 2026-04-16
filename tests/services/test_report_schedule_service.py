"""Тесты ReportScheduleService."""

from datetime import time
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.exc import IntegrityError

from models import ReportSchedule
from repositories.report_schedule_repository import ReportScheduleRepository
from services.report_schedule_service import ReportScheduleService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=ReportScheduleRepository)


@pytest.fixture
def service(mock_repo: AsyncMock) -> ReportScheduleService:
    return ReportScheduleService(schedule_repository=mock_repo)


@pytest.fixture
def sample_schedule() -> MagicMock:
    s = MagicMock(spec=ReportSchedule)
    s.id = 1
    s.chat_id = 1
    s.sent_time = time(9, 0)
    s.enabled = True
    return s


@pytest.mark.asyncio
async def test_get_schedule_returns_schedule(
    service: ReportScheduleService,
    mock_repo: AsyncMock,
    sample_schedule: MagicMock,
) -> None:
    """get_schedule возвращает расписание из репозитория."""
    mock_repo.get_schedule = AsyncMock(return_value=sample_schedule)

    result = await service.get_schedule(chat_id=1)

    assert result is sample_schedule
    mock_repo.get_schedule.assert_called_once_with(chat_id=1)


@pytest.mark.asyncio
async def test_get_schedule_returns_none_when_not_found(
    service: ReportScheduleService,
    mock_repo: AsyncMock,
) -> None:
    """get_schedule возвращает None когда расписание не найдено."""
    mock_repo.get_schedule = AsyncMock(return_value=None)

    result = await service.get_schedule(chat_id=999)

    assert result is None


@pytest.mark.asyncio
async def test_get_or_create_schedule_returns_existing(
    service: ReportScheduleService,
    mock_repo: AsyncMock,
    sample_schedule: MagicMock,
) -> None:
    """get_or_create_schedule возвращает существующее расписание."""
    mock_repo.get_schedule = AsyncMock(return_value=sample_schedule)

    result = await service.get_or_create_schedule(
        chat_id=1, sent_time=time(10, 0)
    )

    assert result is sample_schedule
    mock_repo.create_schedule.assert_not_called()


@pytest.mark.asyncio
async def test_get_or_create_schedule_creates_when_not_found(
    service: ReportScheduleService,
    mock_repo: AsyncMock,
    sample_schedule: MagicMock,
) -> None:
    """get_or_create_schedule создаёт расписание при отсутствии."""
    mock_repo.get_schedule = AsyncMock(return_value=None)
    mock_repo.create_schedule = AsyncMock(return_value=sample_schedule)

    result = await service.get_or_create_schedule(
        chat_id=1,
        sent_time=time(9, 30),
        tz_name="Europe/Moscow",
        enabled=True,
    )

    assert result is sample_schedule
    mock_repo.create_schedule.assert_called_once_with(
        chat_id=1,
        tz_name="Europe/Moscow",
        sent_time=time(9, 30),
        enabled=True,
    )


@pytest.mark.asyncio
async def test_get_or_create_schedule_race_condition_returns_existing(
    service: ReportScheduleService,
    mock_repo: AsyncMock,
    sample_schedule: MagicMock,
) -> None:
    """get_or_create_schedule при IntegrityError возвращает существующее."""
    mock_repo.get_schedule = AsyncMock(side_effect=[None, sample_schedule])
    mock_repo.create_schedule = AsyncMock(
        side_effect=IntegrityError("", "", "unique constraint chat_id")
    )

    result = await service.get_or_create_schedule(
        chat_id=1, sent_time=time(9, 0)
    )

    assert result is sample_schedule
    assert mock_repo.get_schedule.call_count == 2


@pytest.mark.asyncio
async def test_update_sending_time_success(
    service: ReportScheduleService,
    mock_repo: AsyncMock,
    sample_schedule: MagicMock,
) -> None:
    """update_sending_time обновляет время при найденном расписании."""
    updated = MagicMock()
    mock_repo.get_schedule = AsyncMock(return_value=sample_schedule)
    mock_repo.update_schedule = AsyncMock(return_value=updated)

    result = await service.update_sending_time(
        chat_id=1, new_time=time(12, 0)
    )

    assert result is updated
    mock_repo.update_schedule.assert_called_once_with(
        schedule_id=sample_schedule.id, sent_time=time(12, 0)
    )


@pytest.mark.asyncio
async def test_update_sending_time_returns_none_when_not_found(
    service: ReportScheduleService,
    mock_repo: AsyncMock,
) -> None:
    """update_sending_time возвращает None когда расписание не найдено."""
    mock_repo.get_schedule = AsyncMock(return_value=None)

    result = await service.update_sending_time(
        chat_id=999, new_time=time(12, 0)
    )

    assert result is None
    mock_repo.update_schedule.assert_not_called()


@pytest.mark.asyncio
async def test_toggle_schedule_success(
    service: ReportScheduleService,
    mock_repo: AsyncMock,
    sample_schedule: MagicMock,
) -> None:
    """toggle_schedule обновляет enabled при найденном расписании."""
    updated = MagicMock()
    mock_repo.get_schedule = AsyncMock(return_value=sample_schedule)
    mock_repo.update_schedule = AsyncMock(return_value=updated)

    result = await service.toggle_schedule(chat_id=1, enabled=False)

    assert result is updated
    mock_repo.update_schedule.assert_called_once_with(
        schedule_id=sample_schedule.id, enabled=False
    )


@pytest.mark.asyncio
async def test_toggle_schedule_returns_none_when_not_found(
    service: ReportScheduleService,
    mock_repo: AsyncMock,
) -> None:
    """toggle_schedule возвращает None когда расписание не найдено."""
    mock_repo.get_schedule = AsyncMock(return_value=None)

    result = await service.toggle_schedule(chat_id=999, enabled=True)

    assert result is None
    mock_repo.update_schedule.assert_not_called()
