"""Тесты для exceptions/user.py."""

from exceptions.user import UserError, UserNotFoundException


def test_user_error_base() -> None:
    """UserError — базовое исключение для пользователей."""
    exc = UserError("ошибка")
    assert exc.get_user_message() == "ошибка"


def test_user_not_found_exception_get_user_message() -> None:
    """UserNotFoundException возвращает сообщение с identifier."""
    exc = UserNotFoundException(identifier="123")
    assert "123" in exc.get_user_message()
    assert "не найден" in exc.get_user_message().lower()
