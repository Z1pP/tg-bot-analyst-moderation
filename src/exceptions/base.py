from typing import Dict, Optional


class BotBaseException(Exception):
    default_message = "Произошла неожиданная ошибка"

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict] = None,
    ):
        self.message = message or self.default_message
        self.details = details
        super().__init__(self.message)

    @classmethod
    def get_user_message(self) -> str:
        """
        Возращает сообщение для пользователя
        """
        return self.message
