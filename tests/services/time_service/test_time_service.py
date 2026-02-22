"""Тесты для TimeZoneService."""

from datetime import datetime, timezone

from services.time_service import TimeZoneService


def test_convert_to_local_time_none() -> None:
    """None возвращает None."""
    assert TimeZoneService.convert_to_local_time(None) is None


def test_convert_to_local_time_aware() -> None:
    """Timezone-aware datetime конвертируется в локальную зону."""
    utc_dt = datetime(2025, 1, 15, 12, 0, tzinfo=timezone.utc)
    result = TimeZoneService.convert_to_local_time(utc_dt)
    assert result is not None
    assert result.tzinfo is not None


def test_now_returns_aware_datetime() -> None:
    """now() возвращает datetime с tzinfo."""
    result = TimeZoneService.now()
    assert result.tzinfo is not None
