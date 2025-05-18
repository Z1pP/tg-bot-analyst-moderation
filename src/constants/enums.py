from enum import Enum


class ChatType(str, Enum):
    """Типы чатов."""

    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"
    CHANNEL = "channel"
