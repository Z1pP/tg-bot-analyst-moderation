"""Тесты для utils/data_parser.py."""

from datetime import time

from utils.data_parser import (
    MESSAGE_LINK_PATTERN,
    parse_and_validate_tg_id,
    parse_breaks_time,
    parse_duration,
    parse_message_link,
    parse_time,
    parse_tolerance,
)


def test_parse_and_validate_tg_id_valid() -> None:
    """Валидный числовой tg_id возвращается как строка."""
    assert parse_and_validate_tg_id("12345") == "12345"
    assert parse_and_validate_tg_id("  999  ") == "999"


def test_parse_and_validate_tg_id_invalid() -> None:
    """Нечисловые или пустые значения возвращают None."""
    assert parse_and_validate_tg_id("") is None
    assert parse_and_validate_tg_id("   ") is None
    assert parse_and_validate_tg_id("abc") is None
    assert parse_and_validate_tg_id("12.5") is None


def test_parse_message_link_public_chat() -> None:
    """Публичная ссылка на сообщение парсится в @username и message_id."""
    result = parse_message_link("https://t.me/chatname/123")
    assert result == ("@chatname", 123)
    result = parse_message_link("https://t.me/chatname/1/456")
    assert result == ("@chatname", 456)


def test_parse_message_link_private_chat() -> None:
    """Ссылка на сообщение в приватном чате (c/) даёт -100... и message_id."""
    result = parse_message_link("https://t.me/c/1234567890/100")
    assert result[0] == "-1001234567890"
    assert result[1] == 100


def test_parse_message_link_no_match() -> None:
    """Не подходящая строка возвращает None."""
    assert parse_message_link("not a link") is None
    assert parse_message_link("https://example.com/other") is None


def test_parse_time_valid() -> None:
    """Валидное время HH:MM парсится."""
    assert parse_time("09:30") == time(9, 30)
    assert parse_time("00:00") == time(0, 0)
    assert parse_time("23:59") == time(23, 59)


def test_parse_time_invalid() -> None:
    """Неверный формат возвращает None."""
    assert parse_time("25:00") is None
    assert parse_time("12:60") is None
    assert parse_time("invalid") is None
    assert parse_time("") is None


def test_parse_tolerance_valid() -> None:
    """Положительное целое возвращается."""
    assert parse_tolerance("5") == 5
    assert parse_tolerance("  10  ") == 10


def test_parse_tolerance_invalid() -> None:
    """Ноль, отрицательные или не число — None."""
    assert parse_tolerance("0") is None
    assert parse_tolerance("-1") is None
    assert parse_tolerance("") is None
    assert parse_tolerance("  ") is None
    assert parse_tolerance("abc") is None


def test_parse_breaks_time_valid() -> None:
    """Неотрицательное целое для интервала паузы."""
    assert parse_breaks_time("0") == 0
    assert parse_breaks_time("15") == 15


def test_parse_breaks_time_invalid() -> None:
    """Отрицательное или не число — None."""
    assert parse_breaks_time("-1") is None
    assert parse_breaks_time("") is None
    assert parse_breaks_time("x") is None


def test_parse_duration_minutes() -> None:
    """Длительность в минутах (10m) переводится в секунды."""
    assert parse_duration("10m") == 600
    assert parse_duration("1m") == 60


def test_parse_duration_hours_and_days() -> None:
    """Часы и дни."""
    assert parse_duration("2h") == 7200
    assert parse_duration("1d") == 86400


def test_parse_duration_case_insensitive() -> None:
    """Единицы в верхнем регистре тоже принимаются (lower())."""
    assert parse_duration("1M") == 60
    assert parse_duration("1H") == 3600


def test_parse_duration_invalid() -> None:
    """Неверный формат — None."""
    assert parse_duration("") is None
    assert parse_duration("  ") is None
    assert parse_duration("10") is None
    assert parse_duration("10x") is None
    assert parse_duration("m10") is None


def test_message_link_pattern_constant() -> None:
    """Константа паттерна определена."""
    assert MESSAGE_LINK_PATTERN is not None
