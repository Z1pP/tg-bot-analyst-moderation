from .base import BotBaseException


class AmnestyError(BotBaseException):
    """Базовое исключение для ошибок амнистии."""


class UserNotBannedError(AmnestyError):
    """Пользователь не забанен в указанном чате."""

    def __init__(self, username: str, chat_title: str) -> None:
        self.username = username
        self.chat_title = chat_title

    def get_user_message(self) -> str:
        return f"❌ Пользователь @{self.username} не забанен в чате <b>{self.chat_title}</b>."


class UserNotFoundError(AmnestyError):
    """Пользователь не найден в системе."""

    def __init__(self, identifier: str) -> None:
        self.identifier = identifier

    def get_user_message(self) -> str:
        return f"❌ Пользователь {self.identifier} не найден в системе."


class NoChatsWithBannedUserError(AmnestyError):
    """Нет чатов, где пользователь забанен."""

    def __init__(self, username: str) -> None:
        self.username = username

    def get_user_message(self) -> str:
        return f"❌ Нет чатов, где пользователь @{self.username} забанен."


class BotCannotUnbanError(AmnestyError):
    """Бот не может разбанить пользователя (нет прав)."""

    def __init__(self, chat_title: str) -> None:
        self.chat_title = chat_title

    def get_user_message(self) -> str:
        return (
            f"❌ Бот не может разбанить пользователя в чате <b>{self.chat_title}</b>. "
            "Требуются права администратора с возможностью блокировки пользователей."
        )


class UnbanFailedError(AmnestyError):
    """Не удалось разбанить пользователя."""

    def __init__(self, username: str, chat_title: str, reason: str = None) -> None:
        self.username = username
        self.chat_title = chat_title
        self.reason = reason

    def get_user_message(self) -> str:
        base_msg = (
            f"❌ Не удалось разбанить @{self.username} в чате <b>{self.chat_title}</b>."
        )
        if self.reason:
            return f"{base_msg} Причина: {self.reason}"
        return base_msg
