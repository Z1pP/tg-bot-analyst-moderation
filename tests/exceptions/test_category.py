"""Тесты для exceptions/category.py."""

from exceptions.category import CategoryAlreadyExists, CategoryNotFoundError


def test_category_already_exists_get_user_message() -> None:
    """CategoryAlreadyExists возвращает сообщение с именем категории."""
    exc = CategoryAlreadyExists(name="Отчёты")
    assert "Отчёты" in exc.get_user_message()
    assert "уже существует" in exc.get_user_message()


def test_category_not_found_error_get_user_message() -> None:
    """CategoryNotFoundError возвращает фиксированное сообщение."""
    exc = CategoryNotFoundError()
    assert "не найдена" in exc.get_user_message().lower()
