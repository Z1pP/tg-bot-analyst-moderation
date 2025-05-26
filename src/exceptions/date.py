from .base import BotBaseException


class IncorrectDateFormatError(BotBaseException):
    default_message = "Некорректный формат конечной даты. Используйте DD.MM"
