"""Тесты форматирования отображаемого имени нарушителя (логика из utils.moderation)."""

from utils.moderation import format_violator_display


def test_display_name_uses_id_when_username_missing() -> None:
    """Без username возвращается ID:tg_id."""
    assert format_violator_display(None, "123") == "ID:123"


def test_display_name_uses_username_when_present() -> None:
    """С username возвращается @username."""
    assert format_violator_display("user", "123") == "@user"
