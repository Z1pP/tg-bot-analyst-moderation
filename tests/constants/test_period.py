"""Тесты для constants/period.py."""

import sys
from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest

# Устраняем циклический импорт: period -> time_service -> services/__init__ -> taskiq -> period
if "constants.period" not in sys.modules:
    _services_pkg = type(sys)("services")
    _services_pkg.time_service = type(sys)("time_service")
    _services_pkg.time_service.TimeZoneService = MagicMock()
    _orig_services = sys.modules.pop("services", None)
    _orig_sts = sys.modules.pop("services.time_service", None)
    sys.modules["services"] = _services_pkg
    sys.modules["services.time_service"] = _services_pkg.time_service
    from constants.period import SummaryTimePeriod, TimePeriod  # noqa: E402

    if _orig_services is not None:
        sys.modules["services"] = _orig_services
    else:
        del sys.modules["services"]
    if _orig_sts is not None:
        sys.modules["services.time_service"] = _orig_sts
    else:
        del sys.modules["services.time_service"]
else:
    from constants.period import SummaryTimePeriod, TimePeriod


def test_time_period_get_all_periods_excludes_custom() -> None:
    """get_all_periods не включает CUSTOM (только периоды без выбора дат)."""
    periods = TimePeriod.get_all_periods()
    assert TimePeriod.CUSTOM.value not in periods
    assert TimePeriod.TODAY.value in periods
    assert TimePeriod.YESTERDAY.value in periods
    assert TimePeriod.ONE_WEEK.value in periods
    assert TimePeriod.ONE_MONTH.value in periods


def test_time_period_get_all_includes_all() -> None:
    """get_all включает все значения, в том числе CUSTOM."""
    all_periods = TimePeriod.get_all()
    assert TimePeriod.CUSTOM.value in all_periods
    assert len(all_periods) == 5


@patch("constants.period.TimeZoneService")
def test_time_period_to_datetime_today(mock_tz: object) -> None:
    """to_datetime для 'За сегодня' возвращает начало дня и now."""
    fixed = datetime(2025, 2, 20, 14, 30)
    mock_tz.now.return_value = fixed
    start, end = TimePeriod.to_datetime(TimePeriod.TODAY.value)
    assert start == datetime(2025, 2, 20, 0, 0, 0)
    assert end == fixed


@patch("constants.period.TimeZoneService")
def test_time_period_to_datetime_yesterday(mock_tz: object) -> None:
    """to_datetime для 'За вчера' возвращает вчера 00:00 — 23:59:59."""
    fixed = datetime(2025, 2, 20, 12, 0)
    mock_tz.now.return_value = fixed
    start, end = TimePeriod.to_datetime(TimePeriod.YESTERDAY.value)
    assert start == datetime(2025, 2, 19, 0, 0, 0)
    assert end == datetime(2025, 2, 19, 23, 59, 59, 999999)


@patch("constants.period.TimeZoneService")
def test_time_period_to_datetime_one_week(mock_tz: object) -> None:
    """to_datetime для 'За неделю' — 6 дней назад 00:00 и now."""
    fixed = datetime(2025, 2, 20, 10, 0)
    mock_tz.now.return_value = fixed
    start, end = TimePeriod.to_datetime(TimePeriod.ONE_WEEK.value)
    assert start == datetime(2025, 2, 14, 0, 0, 0)
    assert end == fixed


@patch("constants.period.TimeZoneService")
def test_time_period_to_datetime_one_month(mock_tz: object) -> None:
    """to_datetime для 'За месяц' — 29 дней назад 00:00 и now."""
    fixed = datetime(2025, 2, 20, 10, 0)
    mock_tz.now.return_value = fixed
    start, end = TimePeriod.to_datetime(TimePeriod.ONE_MONTH.value)
    assert start == datetime(2025, 1, 22, 0, 0, 0)
    assert end == fixed


def test_time_period_to_datetime_unknown_raises() -> None:
    """Неизвестный период вызывает ValueError."""
    with pytest.raises(ValueError, match="Неизвестный период"):
        TimePeriod.to_datetime("Неизвестный период")


@patch("constants.period.TimeZoneService")
def test_summary_time_period_to_datetime_last_24_hours(mock_tz: object) -> None:
    """SummaryTimePeriod.to_datetime для 'За последние 24 часа'."""
    fixed = datetime(2025, 2, 20, 12, 0)
    mock_tz.now.return_value = fixed
    start, end = SummaryTimePeriod.to_datetime(SummaryTimePeriod.LAST_24_HOURS.value)
    assert (end - start).total_seconds() == 24 * 3600
    assert end == fixed


def test_summary_time_period_to_datetime_unknown_raises() -> None:
    """Неизвестный период сводки вызывает ValueError."""
    with pytest.raises(ValueError, match="Неизвестный период сводки"):
        SummaryTimePeriod.to_datetime("Другое")
