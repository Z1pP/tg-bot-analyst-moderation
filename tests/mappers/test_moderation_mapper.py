"""Тесты для mappers/moderation_mapper.py."""

from unittest.mock import MagicMock, patch

from mappers.moderation_mapper import (
    extract_reason_from_message,
    map_message_to_moderation_dto,
)


def test_extract_reason_from_message_with_reason() -> None:
    """Причина извлекается после первой части команды."""
    message = MagicMock()
    message.text = "/warn Нарушение правил"
    assert extract_reason_from_message(message) == "Нарушение правил"


def test_extract_reason_from_message_no_reason() -> None:
    """Без второй части возвращается None."""
    message = MagicMock()
    message.text = "/warn"
    assert extract_reason_from_message(message) is None


def test_extract_reason_from_message_empty_text() -> None:
    """Пустой text — None."""
    message = MagicMock()
    message.text = None
    assert extract_reason_from_message(message) is None


def test_extract_reason_from_message_single_word() -> None:
    """Одно слово без пробела — None."""
    message = MagicMock()
    message.text = "command"
    assert extract_reason_from_message(message) is None


@patch("mappers.moderation_mapper.TimeZoneService")
def test_map_message_to_moderation_dto(mock_tz: MagicMock) -> None:
    """Маппинг сообщения в ModerationActionDTO."""
    mock_tz.convert_to_local_time.side_effect = lambda dt: dt

    message = MagicMock()
    message.text = "/warn Причина"
    message.from_user = MagicMock()
    message.from_user.id = 111
    message.from_user.username = "admin_user"
    message.chat = MagicMock()
    message.chat.id = -100123
    message.chat.title = "Test Chat"
    message.message_id = 2
    message.date = __import__("datetime").datetime(2025, 1, 1, 12, 0)

    message.reply_to_message = MagicMock()
    message.reply_to_message.from_user = MagicMock()
    message.reply_to_message.from_user.id = 222
    message.reply_to_message.from_user.username = "violator"
    message.reply_to_message.message_id = 1
    message.reply_to_message.date = __import__("datetime").datetime(2025, 1, 1, 11, 0)

    result = map_message_to_moderation_dto(message)

    assert result.violator_tgid == "222"
    assert result.violator_username == "violator"
    assert result.admin_username == "admin_user"
    assert result.admin_tgid == "111"
    assert result.chat_tgid == "-100123"
    assert result.chat_title == "Test Chat"
    assert result.reply_message_id == 1
    assert result.original_message_id == 2
    assert result.reason == "Причина"
    mock_tz.convert_to_local_time.assert_called()
