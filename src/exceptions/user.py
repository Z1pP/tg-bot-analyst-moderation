from .base import BotBaseException


class UserNotFoundException(BotBaseException):
    default_message = "❌ Пользователь не найден в базе данных."
