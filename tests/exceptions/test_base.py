"""Тесты для exceptions/base.py."""

from exceptions.base import BotBaseException


def test_bot_base_exception_default_message() -> None:
    """Без аргументов используется default_message."""
    exc = BotBaseException()
    assert str(exc) == "Произошла неожиданная ошибка"
    assert exc.get_user_message() == "Произошла неожиданная ошибка"


def test_bot_base_exception_custom_message() -> None:
    """С message переданное сообщение сохраняется."""
    exc = BotBaseException("Кастомное сообщение")
    assert exc.message == "Кастомное сообщение"
    assert exc.get_user_message() == "Кастомное сообщение"


def test_bot_base_exception_with_details() -> None:
    """details сохраняются в атрибуте."""
    exc = BotBaseException("Ошибка", details={"key": "value"})
    assert exc.details == {"key": "value"}
    assert exc.get_user_message() == "Ошибка"
