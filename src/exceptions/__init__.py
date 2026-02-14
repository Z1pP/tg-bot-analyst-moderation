from .amnesty import (
    AmnestyError,
    BotCannotUnbanError,
    NoChatsWithBannedUserError,
    UnbanFailedError,
    UserNotBannedError,
)
from .amnesty import (
    UserNotFoundError as AmnestyUserNotFoundError,
)
from .base import BotBaseException
from .moderation import (
    ArchiveChatError,
    BotInsufficientPermissionsError,
    CannotPunishBotAdminError,
    CannotPunishChatAdminError,
    CannotPunishYouSelf,
    MessageTooOldError,
    ModerationError,
    PrivateModerationError,
    PublicModerationError,
)
from .user import UserError, UserNotFoundException


# Database exceptions
class DatabaseException(BotBaseException):
    default_message = "Ошибка работы с базой данных"


class UserNotFoundError(DatabaseException):
    default_message = "❌ Пользователь не найден"


class ChatNotFoundException(DatabaseException):
    default_message = "❌ Чат не найден"


class DuplicateRecordException(DatabaseException):
    default_message = "❌ Запись уже существует"


# Validation exceptions
class ValidationException(BotBaseException):
    default_message = "❌ Неверные данные"


class InvalidUsernameException(ValidationException):
    default_message = "❌ Неверный формат username"


class InvalidUserIdException(ValidationException):
    default_message = "❌ Неверный формат ID пользователя"


# Telegram API exceptions
class TelegramApiException(BotBaseException):
    default_message = "❌ Ошибка Telegram API"


class UserNotInChatException(TelegramApiException):
    default_message = "❌ Пользователь не найден в чате"


class BotPermissionException(TelegramApiException):
    default_message = "❌ Недостаточно прав у бота"


# Business logic exceptions
class BusinessLogicException(BotBaseException):
    default_message = "❌ Ошибка выполнения операции"


class UserAlreadyTrackedException(BusinessLogicException):
    default_message = "❌ Пользователь уже отслеживается"


class EmptyTrackingListException(BusinessLogicException):
    default_message = "❌ У вас нет отслеживаемых чатов"


class AdminLogsError(BotBaseException):
    """Ошибка при получении логов администраторов."""

    default_message = "⚠️ Произошла ошибка при получении логов."


class ReleaseNoteNotFoundError(BotBaseException):
    """Релизная заметка не найдена."""

    default_message = "❌ Заметка не найдена"


class ReleaseNoteError(BotBaseException):
    """Ошибка при работе с релизными заметками."""

    default_message = "❌ Ошибка при работе с заметкой"


__all__ = [
    "AmnestyError",
    "BotCannotUnbanError",
    "NoChatsWithBannedUserError",
    "UnbanFailedError",
    "UserNotBannedError",
    "AmnestyUserNotFoundError",
    "BotBaseException",
    "ArchiveChatError",
    "BotInsufficientPermissionsError",
    "CannotPunishBotAdminError",
    "CannotPunishChatAdminError",
    "CannotPunishYouSelf",
    "MessageTooOldError",
    "ModerationError",
    "PrivateModerationError",
    "PublicModerationError",
    "UserError",
    "UserNotFoundException",
    "DatabaseException",
    "UserNotFoundError",
    "AdminLogsError",
    "ReleaseNoteNotFoundError",
    "ReleaseNoteError",
]
