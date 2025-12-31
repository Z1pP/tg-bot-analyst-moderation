from enum import Enum


class ChatType(str, Enum):
    """Типы чатов."""

    PRIVATE = "private"
    GROUP = "group"
    SUPERGROUP = "supergroup"


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

    # REPORT ACTIONS
    REPORT_USER = "report_user"
    REPORT_CHAT = "report_chat"
    REPORT_ALL_USERS = "report_all_users"
    # TEMPLATE ACTIONS
    ADD_TEMPLATE = "add_template"
    DELETE_TEMPLATE = "delete_template"
    ADD_CATEGORY = "add_category"
    DELETE_CATEGORY = "delete_category"
    # MESSAGE ACTIONS
    SEND_MESSAGE = "send_message"
    DELETE_MESSAGE = "delete_message"
    REPLY_MESSAGE = "reply_message"
    # MODERATION ACTIONS
    CANCEL_LAST_WARN = "cancel_last_warn"
    UNMUTE_USER = "unmute_user"
    UNBAN_USER = "unban_user"
    WARN_USER = "warn_user"
    BAN_USER = "ban_user"
    # PERMISSIONS ACTIONS
    UPDATE_PERMISSIONS = "update_permissions"
    # CHAT ACTIONS
    ADD_CHAT = "add_chat"
    REMOVE_CHAT = "remove_chat"
    GET_CHAT_DAILY_RATING = "get_chat_daily_rating"
    GET_CHAT_SUMMARY_24H = "get_chat_summary_24h"
    REPORT_TIME_SETTING = "report_time_setting"
    PUNISHMENT_SETTING = "punishment_setting"
    # ADMIN ACTIONS
    ADD_USER = "add_user"
    REMOVE_USER = "remove_user"


class SummaryType(str, Enum):
    """Типы сводок."""

    SHORT = "short"
    FULL = "full"
