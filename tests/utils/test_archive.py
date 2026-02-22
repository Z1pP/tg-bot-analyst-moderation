"""Тесты для utils/archive.py."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from utils.archive import build_schedule_info


def test_build_schedule_info_none() -> None:
    """При schedule=None возвращается выключено и текст про не настроена."""
    schedule_info, enabled = build_schedule_info(None)
    assert enabled is False
    assert "Выключена" in schedule_info
    assert "не настроена" in schedule_info


def test_build_schedule_info_disabled() -> None:
    """При schedule.enabled=False — выключена, без следующей рассылки."""
    schedule = SimpleNamespace(enabled=False, next_run_at=None)
    schedule_info, enabled = build_schedule_info(schedule)
    assert enabled is False
    assert "Выключена" in schedule_info


def test_build_schedule_info_enabled_no_next_run() -> None:
    """При enabled=True и next_run_at=None — текст 'не запланирована'."""
    schedule = SimpleNamespace(enabled=True, next_run_at=None)
    schedule_info, enabled = build_schedule_info(schedule)
    assert enabled is True
    assert "Включена" in schedule_info
    assert "не запланирована" in schedule_info


def test_build_schedule_info_enabled_with_next_run() -> None:
    """При enabled=True и next_run_at задан — форматируется локальное время."""
    schedule = SimpleNamespace(
        enabled=True,
        next_run_at=datetime(2025, 2, 20, 10, 30),
    )
    with patch(
        "utils.archive.TimeZoneService.convert_to_local_time",
        return_value=datetime(2025, 2, 20, 13, 30),
    ):
        schedule_info, enabled = build_schedule_info(schedule)
    assert enabled is True
    assert "Следующая рассылка" in schedule_info
    assert "20.02.2025" in schedule_info or "13:30" in schedule_info
