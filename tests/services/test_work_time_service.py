"""Тесты WorkTimeService: работа с необязательными настройками чата."""

from datetime import datetime

from services.work_time_service import WorkTimeService


def test_adjust_dates_uses_defaults_when_settings_are_none() -> None:
    """Без настроек чата берутся START_TIME/END_TIME/TOLERANCE."""
    start = datetime(2025, 1, 15, 0, 0)
    end = datetime(2025, 1, 15, 23, 59)

    adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
        start_date=start,
        end_date=end,
        work_start=None,
        work_end=None,
        tolerance=None,
    )

    assert (adjusted_start.hour, adjusted_start.minute) == (9, 50)
    assert (adjusted_end.hour, adjusted_end.minute) == (22, 10)


def test_adjust_dates_uses_chat_settings() -> None:
    """Переданные настройки чата имеют приоритет над константами."""
    start = datetime(2025, 1, 15, 0, 0)
    end = datetime(2025, 1, 15, 23, 59)

    adjusted_start, adjusted_end = WorkTimeService.adjust_dates_to_work_hours(
        start_date=start,
        end_date=end,
        work_start=None,
        work_end=None,
        tolerance=30,
    )

    assert (adjusted_start.hour, adjusted_start.minute) == (9, 30)