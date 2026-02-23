"""Тесты для exceptions/moderation.py."""

from exceptions.moderation import (
    ArchiveChatError,
    BotInsufficientPermissionsError,
    BotNoAdminRightsInArchiveChatError,
    BotNotInArchiveChatError,
    CannotPunishBotAdminError,
    CannotPunishChatAdminError,
    CannotPunishYouSelf,
    MessageDeleteError,
    MessageSendError,
    MessageTooOldError,
    ModerationError,
    PrivateModerationError,
    PublicModerationError,
)


def test_moderation_error_base() -> None:
    """ModerationError — базовый класс, наследует BotBaseException."""
    exc = ModerationError("тест")
    assert exc.get_user_message() == "тест"


def test_private_moderation_error_inherits() -> None:
    """PrivateModerationError наследует ModerationError."""
    exc = PrivateModerationError("в ЛС")
    assert exc.get_user_message() == "в ЛС"


def test_public_moderation_error_inherits() -> None:
    """PublicModerationError наследует ModerationError."""
    exc = PublicModerationError("в чат")
    assert exc.get_user_message() == "в чат"


def test_bot_insufficient_permissions_error_get_user_message() -> None:
    """BotInsufficientPermissionsError возвращает сообщение с chat_title."""
    exc = BotInsufficientPermissionsError(chat_title="Чат")
    msg = exc.get_user_message()
    assert "Чат" in msg
    assert "прав" in msg


def test_archive_chat_error_get_user_message() -> None:
    """ArchiveChatError возвращает подсказку про архивный чат."""
    exc = ArchiveChatError(chat_title="Рабочий чат")
    assert "Рабочий чат" in exc.get_user_message()
    assert "архив" in exc.get_user_message().lower() or "чат" in exc.get_user_message()


def test_cannot_punish_chat_admin_error_get_user_message() -> None:
    """CannotPunishChatAdminError возвращает фиксированный текст."""
    exc = CannotPunishChatAdminError()
    assert "администратор" in exc.get_user_message().lower()


def test_cannot_punish_bot_admin_error_get_user_message() -> None:
    """CannotPunishBotAdminError возвращает фиксированный текст."""
    exc = CannotPunishBotAdminError()
    assert "нельзя" in exc.get_user_message().lower()


def test_cannot_punish_you_self_get_user_message() -> None:
    """CannotPunishYouSelf возвращает фиксированный текст."""
    exc = CannotPunishYouSelf()
    assert "нельзя" in exc.get_user_message().lower()


def test_message_too_old_error_get_user_message() -> None:
    """MessageTooOldError — сообщение про 48 часов."""
    exc = MessageTooOldError()
    assert "48" in exc.get_user_message()


def test_message_delete_error_get_user_message() -> None:
    """MessageDeleteError — сообщение про удаление."""
    exc = MessageDeleteError()
    assert "удалить" in exc.get_user_message().lower()


def test_message_send_error_get_user_message() -> None:
    """MessageSendError сохраняет error и возвращает фиксированный текст."""
    exc = MessageSendError(error="Network error")
    assert exc.error == "Network error"
    assert "отправить" in exc.get_user_message().lower()


def test_bot_no_admin_rights_in_archive_chat_error_get_user_message() -> None:
    """BotNoAdminRightsInArchiveChatError — сообщение с названием чата."""
    exc = BotNoAdminRightsInArchiveChatError(archive_chat_title="Архив")
    assert "Архив" in exc.get_user_message()
    assert "администратор" in exc.get_user_message().lower()


def test_bot_not_in_archive_chat_error_get_user_message() -> None:
    """BotNotInArchiveChatError — сообщение с названием чата."""
    exc = BotNotInArchiveChatError(archive_chat_title="Архив")
    assert "Архив" in exc.get_user_message()
    assert (
        "добавьте" in exc.get_user_message().lower() or "чат" in exc.get_user_message()
    )
