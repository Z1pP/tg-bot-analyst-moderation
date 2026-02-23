"""Тесты для исключений из exceptions/__init__.py (Database, Validation, Telegram, BusinessLogic)."""

from exceptions import (
    AdminLogsError,
    BotPermissionException,
    BusinessLogicException,
    ChatNotFoundException,
    DatabaseException,
    DuplicateRecordException,
    EmptyTrackingListException,
    InvalidUserIdException,
    InvalidUsernameException,
    UserAlreadyTrackedException,
    UserNotFoundError,
    UserNotInChatException,
    ValidationException,
)


def test_database_exception_default_message() -> None:
    """DatabaseException имеет default_message."""
    exc = DatabaseException()
    assert (
        "баз" in exc.get_user_message().lower()
        or "данн" in exc.get_user_message().lower()
    )


def test_user_not_found_error_default_message() -> None:
    """UserNotFoundError (DB) — сообщение про пользователя."""
    exc = UserNotFoundError()
    assert (
        "пользователь" in exc.get_user_message().lower()
        or "найден" in exc.get_user_message().lower()
    )


def test_chat_not_found_exception() -> None:
    """ChatNotFoundException — сообщение про чат."""
    exc = ChatNotFoundException()
    assert "чат" in exc.get_user_message().lower()


def test_duplicate_record_exception() -> None:
    """DuplicateRecordException — сообщение про запись."""
    exc = DuplicateRecordException()
    assert (
        "существует" in exc.get_user_message().lower()
        or "запис" in exc.get_user_message().lower()
    )


def test_validation_exception() -> None:
    """ValidationException — сообщение про данные."""
    exc = ValidationException()
    assert (
        "данн" in exc.get_user_message().lower()
        or "неверн" in exc.get_user_message().lower()
    )


def test_invalid_username_exception() -> None:
    """InvalidUsernameException — про username."""
    exc = InvalidUsernameException()
    assert (
        "username" in exc.get_user_message().lower()
        or "формат" in exc.get_user_message().lower()
    )


def test_invalid_user_id_exception() -> None:
    """InvalidUserIdException — про ID."""
    exc = InvalidUserIdException()
    assert (
        "id" in exc.get_user_message().lower()
        or "формат" in exc.get_user_message().lower()
    )


def test_user_not_in_chat_exception() -> None:
    """UserNotInChatException — пользователь не в чате."""
    exc = UserNotInChatException()
    assert "чат" in exc.get_user_message().lower()


def test_bot_permission_exception() -> None:
    """BotPermissionException — права бота."""
    exc = BotPermissionException()
    assert "прав" in exc.get_user_message().lower()


def test_business_logic_exception() -> None:
    """BusinessLogicException — ошибка операции."""
    exc = BusinessLogicException()
    assert (
        "операц" in exc.get_user_message().lower()
        or "ошибка" in exc.get_user_message().lower()
    )


def test_user_already_tracked_exception() -> None:
    """UserAlreadyTrackedException — уже отслеживается."""
    exc = UserAlreadyTrackedException()
    assert "отслежива" in exc.get_user_message().lower()


def test_empty_tracking_list_exception() -> None:
    """EmptyTrackingListException — нет отслеживаемых чатов."""
    exc = EmptyTrackingListException()
    assert (
        "отслежива" in exc.get_user_message().lower()
        or "нет" in exc.get_user_message().lower()
    )


def test_admin_logs_error() -> None:
    """AdminLogsError — ошибка при получении логов."""
    exc = AdminLogsError()
    assert (
        "лог" in exc.get_user_message().lower()
        or "ошибка" in exc.get_user_message().lower()
    )
