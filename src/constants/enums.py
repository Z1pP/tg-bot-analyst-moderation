from enum import Enum


class ChatType(str, Enum):
    """Типы чатов."""

    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"


class UserRole(Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


class ReactionAction(str, Enum):
    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"
