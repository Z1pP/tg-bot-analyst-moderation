from .base import BotBaseException


class UserError(BotBaseException):
    """Базовое исключение для ошибок пользователей."""


class UserNotFoundException(UserError):
    """Пользователь не найден в базе данных."""
    
    def __init__(self, identifier: str) -> None:
        self.identifier = identifier
    
    def get_user_message(self) -> str:
        return f"❌ Пользователь {self.identifier} не найден в базе данных."
