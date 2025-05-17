from .base import BotBaseException


class userNotFoundException(BotBaseException):
    default_message = "❌ Пользователь не найден в базе данных."
