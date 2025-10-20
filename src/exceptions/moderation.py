from .base import BotBaseException


class ModerationError(BotBaseException):
    """Базовое исключение для ошибок модерации."""


class PublicModerationError(ModerationError):
    """Исключение, текст которого будет отправляться в чат"""


class PrivateModerationError(ModerationError):
    """Исключение, текст которого будет отправляться в ЛС админу"""


class BotInsufficientPermissionsError(PrivateModerationError):
    """Бот не имеет необходимых прав для модерации"""

    def __init__(self, chat_title: str) -> None:
        self.chat_title = chat_title

    def get_user_message(self):
        return (
            f"❌ Бот не имеет необходимых прав для модерации в чате <b>{self.chat_title}</b>. "
            "Требуются права: удаление сообщений, блокировка пользователей."
        )


class ArchiveChatError(PrivateModerationError):
    """Проблема с архивным чатом."""

    def __init__(self, chat_title: str):
        self.chat_title = chat_title

    def get_user_message(self) -> str:
        return (
            "Пожалуйста, создайте рабочий чат с историей удалённых сообщений, "
            f"добавьте в него  Аналиста и привяжите его к чату <b>{self.chat_title}</b>.\n"
            "В будущем это облегчит работу при поиске заблокированных пользователей."
        )


class CannotPunishChatAdminError(PrivateModerationError):
    """Попытка наказать другого администратора."""

    def get_user_message(self) -> str:
        return "❌ Данный пользователь является администратором чата – наказание невозможно."


class CannotPunishBotAdminError(PrivateModerationError):
    """Попытка наказать бота администратора."""

    def get_user_message(self) -> str:
        return "❌ Данный пользователь является администратором бота – наказание невозможно."


class CannotPunishYouSelf(PrivateModerationError):
    """Попытка наказать самого себя."""

    def get_user_message(self) -> str:
        return "❌ Нельзя применить наказание к себе - наказание невозможно"


class MessageTooOldError(PrivateModerationError):
    """Сообщение слишком старое для удаления."""

    def get_user_message(self) -> str:
        return (
            "❌ Не удалось удалить исходное сообщение, так как оно было отправлено "
            "более 48 часов назад."
        )
