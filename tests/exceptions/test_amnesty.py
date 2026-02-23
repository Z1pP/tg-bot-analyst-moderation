"""Тесты для exceptions/amnesty.py."""

from exceptions.amnesty import (
    BotCannotUnbanError,
    NoChatsWithBannedUserError,
    UnbanFailedError,
    UserNotBannedError,
)
from exceptions.amnesty import UserNotFoundError as AmnestyUserNotFoundError


def test_user_not_banned_error_get_user_message() -> None:
    """UserNotBannedError возвращает сообщение с username и chat_title."""
    exc = UserNotBannedError(username="john", chat_title="Чат")
    assert "john" in exc.get_user_message()
    assert "Чат" in exc.get_user_message()
    assert "не забанен" in exc.get_user_message()


def test_amnesty_user_not_found_error_get_user_message() -> None:
    """Amnesty UserNotFoundError возвращает сообщение с identifier."""
    exc = AmnestyUserNotFoundError(identifier="@john")
    assert "john" in exc.get_user_message()
    assert "не найден" in exc.get_user_message()


def test_no_chats_with_banned_user_error_get_user_message() -> None:
    """NoChatsWithBannedUserError возвращает сообщение с username."""
    exc = NoChatsWithBannedUserError(username="user")
    assert "user" in exc.get_user_message()
    assert "забанен" in exc.get_user_message()


def test_bot_cannot_unban_error_get_user_message() -> None:
    """BotCannotUnbanError возвращает сообщение о правах."""
    exc = BotCannotUnbanError(chat_title="Архив")
    assert "Архив" in exc.get_user_message()
    assert "разбанить" in exc.get_user_message()
    assert "администратора" in exc.get_user_message()


def test_unban_failed_error_get_user_message_without_reason() -> None:
    """UnbanFailedError без reason — базовое сообщение."""
    exc = UnbanFailedError(username="u", chat_title="C")
    msg = exc.get_user_message()
    assert "u" in msg and "C" in msg
    assert "Причина:" not in msg


def test_unban_failed_error_get_user_message_with_reason() -> None:
    """UnbanFailedError с reason — сообщение содержит причину."""
    exc = UnbanFailedError(username="u", chat_title="C", reason="Нет прав")
    msg = exc.get_user_message()
    assert "Причина:" in msg
    assert "Нет прав" in msg
