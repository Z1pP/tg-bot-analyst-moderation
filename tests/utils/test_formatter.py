"""Тесты для utils/formatter.py."""

from datetime import datetime

from utils.formatter import (
    format_duration,
    format_seconds,
    format_selected_period,
)


def test_format_selected_period_single_day() -> None:
    """Один и тот же день форматируется как одна дата."""
    start = datetime(2025, 2, 15, 10, 0)
    end = datetime(2025, 2, 15, 18, 0)
    assert format_selected_period(start, end) == "15 февр."


def test_format_selected_period_range() -> None:
    """Период в разные дни — две даты через дефис."""
    start = datetime(2025, 2, 10, 0, 0)
    end = datetime(2025, 2, 20, 0, 0)
    assert format_selected_period(start, end) == "10 февр. - 20 февр."


def test_format_selected_period_different_months() -> None:
    """Период захватывает два месяца."""
    start = datetime(2025, 1, 28, 0, 0)
    end = datetime(2025, 2, 5, 0, 0)
    assert format_selected_period(start, end) == "28 янв. - 5 февр."


def test_format_duration_less_than_one_second() -> None:
    """Меньше секунды — '0 сек.'."""
    assert format_duration(0.5) == "0 сек."
    assert format_duration(0) == "0 сек."


def test_format_duration_seconds_only() -> None:
    """Только секунды."""
    assert format_duration(45) == "45 сек."
    assert format_duration(1) == "1 сек."


def test_format_duration_minutes_and_seconds() -> None:
    """Минуты и секунды."""
    assert format_duration(90) == "1 мин. 30 сек."
    assert format_duration(125) == "2 мин. 5 сек."


def test_format_duration_hours() -> None:
    """Часы, минуты, секунды."""
    assert format_duration(3661) == "1 ч. 1 мин. 1 сек."
    assert format_duration(7200) == "2 ч."


def test_format_duration_with_days() -> None:
    """С include_days=True отображаются дни."""
    assert format_duration(86400) == "1 д."
    assert format_duration(90061) == "1 д. 1 ч. 1 мин. 1 сек."


def test_format_duration_without_days() -> None:
    """С include_days=False дни не выделяются (только часы и ниже)."""
    assert format_duration(86400, include_days=False) == "24 ч."
    assert format_duration(90061, include_days=False) == "25 ч. 1 мин. 1 сек."


def test_format_seconds_alias() -> None:
    """format_seconds — псевдоним без дней."""
    assert format_seconds(3661) == "1 ч. 1 мин. 1 сек."
    assert format_seconds(86400) == "24 ч."
