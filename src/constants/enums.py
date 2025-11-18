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


class AdminActionType(str, Enum):
    """Типы действий администраторов для логирования."""

    REPORT_USER = "report_user"
    REPORT_CHAT = "report_chat"
    REPORT_ALL_USERS = "report_all_users"
    ADD_TEMPLATE = "add_template"
    DELETE_TEMPLATE = "delete_template"
    ADD_CATEGORY = "add_category"
    DELETE_CATEGORY = "delete_category"
    SEND_MESSAGE = "send_message"
    DELETE_MESSAGE = "delete_message"
    REPLY_MESSAGE = "reply_message"
    CHANGE_USER_ROLE = "change_user_role"
