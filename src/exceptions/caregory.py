from .base import BotBaseException


class CategoryAlreadyExists(BotBaseException):
    """Категория с таким именем уже существует."""

    def __init__(self, name: str) -> None:
        self.name = name

    def get_user_message(self) -> str:
        return f"❌ Категория <b>{self.name}</b> уже существует."
