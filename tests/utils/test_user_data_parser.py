"""Тесты для utils/user_data_parser.py."""

from utils.user_data_parser import UserData, parse_data_from_text


def test_parse_data_from_text_username() -> None:
    """Строка с @ даёт UserData с username (без @)."""
    result = parse_data_from_text("@john")
    assert result is not None
    assert result.username == "john"
    assert result.tg_id is None


def test_parse_data_from_text_tg_id() -> None:
    """Чисто цифровая строка даёт UserData с tg_id."""
    result = parse_data_from_text("12345")
    assert result is not None
    assert result.tg_id == "12345"
    assert result.username is None


def test_parse_data_from_text_invalid() -> None:
    """Не username и не число — None."""
    assert parse_data_from_text("john") is None
    assert parse_data_from_text("abc123") is None
    assert parse_data_from_text("") is None


def test_user_data_dataclass_defaults() -> None:
    """UserData имеет поля username и tg_id по умолчанию None."""
    u = UserData()
    assert u.username is None
    assert u.tg_id is None
