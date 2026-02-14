class ChatCallbackData:
    """Класс для хранения callback данных чата"""

    # Commands
    MANAGEMENT = "chats_management"
    ADD = "add_chat"
    REMOVE = "remove_chat"
    GET_REPORT = "get_chat_report"
    GET_DAILY_RATING = "get_chat_daily_rating"
    GET_CHAT_SUMMARY_24H = "get_chat_summary_24h"
    SELECT_CHAT_FOR_REPORT = "select_chat_for_report"
    SELECT_CHAT_FOR_SETTINGS = "select_chat_for_settings"
    REPORT_TIME_SETTING = "report_time_setting"
    CHECK_PERMISSIONS = "check_permissions"
    CHANGE_WORK_START = "change_work_start"
    CHANGE_WORK_END = "change_work_end"
    CHANGE_TOLERANCE = "change_tolerance"
    CHANGE_BREAKS_TIME = "change_breaks_time"
    CANCEL_TIME_SETTING = "cancel_work_hours_setting"
    ARCHIVE_SETTING = "archive_setting"
    ARCHIVE_BIND_INSTRUCTION = "archive_bind_instruction"
    ARCHIVE_TIME_SETTING = "archive_time_setting"
    ARCHIVE_TOGGLE_SCHEDULE = "archive_toggle_schedule"
    BACK_TO_CHAT_ACTIONS = "back_to_chat_actions"
    BACK_TO_ANALYTICS_CHAT_ACTIONS = "back_to_analytics_chat_actions"
    SHOW_MENU = "chats_menu"
    BACK_TO_MAIN_MENU_FROM_CHATS = "back_to_main_menu_from_chats"
    PUNISHMENT_SETTING = "punishment_setting"
    PUNISHMENT_CREATE_NEW = "punishment_create_new"
    PUNISHMENT_SET_DEFAULT = "punishment_set_default"
    CANCEL_SET_DEFAULT = "punishment_set_default_cancel"
    CONFIRM_SET_DEFAULT = "punishment_set_default_confirm"
    PUNISH_ACTION_WARNING = "punish_action_warning"
    PUNISH_ACTION_MUTE = "punish_action_mute"
    PUNISH_ACTION_BAN = "punish_action_ban"
    PUNISH_STEP_NEXT = "punish_step_next"
    PUNISH_STEP_SAVE = "punish_step_save"
    PUNISH_STEP_CANCEL = "punish_step_cancel"
    ANTIBOT_TOGGLE = "chat_antibot_toggle"
    ANTIBOT_SETTING = "chat_antibot_setting"
    WELCOME_TEXT_SETTING = "chat_welcome_text_setting"
    WELCOME_TEXT_TOGGLE = "chat_welcome_text_toggle"
    AUTO_DELETE_TOGGLE = "chat_auto_delete_toggle"
    CHANGE_WELCOME_TEXT = "chat_change_welcome_text"
    ALL_CHATS = "chat__all"
    CHATS_PAGE_INFO = "chats_page_info"
    REMOVE_CHATS_PAGE_INFO = "remove_chats_page_info"

    # Prefixes
    PREFIX_CHAT = "chat__"
    PREFIX_CHAT_SUMMARY_TYPE = "chat_summary_type__"
    PREFIX_UNTRACK_CHAT = "untrack_chat__"
    PREFIX_CONFIRM_REMOVE_CHAT = "conf_remove_chat__"
    PREFIX_PUNISH_ACTION = "punish_action_"
    PREFIX_TEMPLATE_SCOPE = "template_scope__"
    PREFIX_PREV_CHATS_PAGE = "prev_chats_page__"
    PREFIX_NEXT_CHATS_PAGE = "next_chats_page__"
    PREFIX_PREV_CHATS_REPORT_PAGE = "prev_chats_report_page__"
    PREFIX_NEXT_CHATS_REPORT_PAGE = "next_chats_report_page__"
    PREFIX_PREV_REMOVE_CHATS_PAGE = "prev_remove_chats_page__"
    PREFIX_NEXT_REMOVE_CHATS_PAGE = "next_remove_chats_page__"


class ReportCallbackData:
    """Класс для хранения callback данных отчетов"""

    # Commands
    GET_USER_REPORT = "get_user_report"
    GET_ALL_USERS_REPORT = "get_all_users_report"
    BACK_TO_PERIODS = "back_to_periods"
    ORDER_DETAILS = "order_details"
    BACK_TO_SINGLE_USER_ACTIONS = "back_to_single_user_actions"
    BACK_TO_ALL_USERS_ACTIONS = "back_to_all_users_actions"

    # Prefixes
    PREFIX_PERIOD = "period__"
    PREFIX_HIDE_DETAILS = "hide_details_"
    PREFIX_CALENDAR = "cal_"


class UserCallbackData:
    """Класс для хранения callback данных пользователей"""

    # Commands
    SHOW_MENU = "users_menu"
    SHOW_TRACKED_USERS_LIST = "show_tracked_users_list"
    ADD = "add_user"
    REMOVE = "remove_user"
    SELECT_USER_FOR_REPORT = "select_user_for_report"
    BACK_TO_MAIN_MENU_FROM_USERS = "back_to_main_menu_from_users"
    ALL_USERS = "all_users"
    USERS_PAGE_INFO = "users_page_info"
    REMOVE_USERS_PAGE_INFO = "remove_users_page_info"
    MANAGEMENT = "users_management"

    # Prefixes
    PREFIX_USER = "user__"
    PREFIX_REMOVE_USER = "remove_user__"
    PREFIX_CONFIRM_REMOVE_USER = "conf_remove_user__"
    PREFIX_PREV_USERS_PAGE = "prev_users_page__"
    PREFIX_NEXT_USERS_PAGE = "next_users_page__"
    PREFIX_PREV_REMOVE_USERS_PAGE = "prev_remove_users_page__"
    PREFIX_NEXT_REMOVE_USERS_PAGE = "next_remove_users_page__"
    PREFIX_ROLE_SELECT = "role_select__"


class MenuCallbackData:
    """Класс для хранения callback данных главного меню"""

    # Commands
    CHATS_MENU = "chats_menu"
    MAIN_MENU = "main_menu"
    HIDE_NOTIFICATION = "hide_notification"
    SHOW_MENU = "main_menu"


class AdminLogsCallbackData:
    """Класс для хранения callback данных логов администраторов"""

    # Commands
    SHOW_MENU = "admin_logs_menu"
    SELECT_ADMIN = "admin_logs_select_admin"


class ReleaseNotesCallbackData:
    """Класс для хранения callback данных релизных заметок"""

    # Commands
    SHOW_MENU = "release_notes_menu"
    ADD = "add_release_note"
    BACK = "back_to_release_notes"
    PAGE_INFO = "release_notes_page_info"
    EDIT = "edit_release_note"
    DELETE = "delete_release_note"
    EDIT_TITLE = "edit_release_note_title"
    EDIT_CONTENT = "edit_release_note_content"
    CANCEL_EDIT = "cancel_edit_release_note"
    BROADCAST = "broadcast_release_note"
    CANCEL_ADD = "cancel_add_release_note"
    CHANGE_TITLE_WHILE_ADDING = "change_title_while_adding_release_note"

    # Prefixes
    PREFIX_SELECT = "release_note__"
    PREFIX_PREV_PAGE = "prev_release_notes_page__"
    PREFIX_NEXT_PAGE = "next_release_notes_page__"
    PREFIX_CONFIRM_DELETE = "conf_delete_release_note__"
    PREFIX_CONFIRM_BROADCAST = "conf_broadcast_release_note__"
    PREFIX_SELECT_LANGUAGE = "select_language__"
    PREFIX_SELECT_ADD_LANGUAGE = "select_add_language__"


class RoleCallbackData:
    """Класс для хранения callback данных ролей"""

    # Commands
    INPUT_USER_DATA = "input_user_data"


class ModerationCallbackData:
    """Класс для хранения callback данных модерации"""

    # Commands
    SHOW_MENU = "moderation_menu"
    NO_REASON = "no_reason"
    CONFIRM_ACTION = "confirm_moderation_action"
    CANCEL_ACTION = "cancel_moderation_action"


class AnalyticsCallbackData:
    """Класс для хранения callback данных аналитики"""

    # Commands
    SHOW_MENU = "analytics_menu"


class MessagesCallbackData:
    """Класс для хранения callback данных сообщений"""

    # Commands
    SHOW_MENU = "message_management_menu"
    DELETE_MESSAGE = "delete_message"
    REPLY_MESSAGE = "reply_message"
    CANCEL = "cancel"
    CANCEL_REPLY = "cancel_reply_message"
    DELETE_MESSAGE_CONFIRM = "delete_message_confirm"
    DELETE_MESSAGE_CANCEL = "delete_message_cancel"
    SEND_MESSAGE_TO_CHAT = "send_message_to_chat"
    SELECT_ALL_CHATS = "select_chat_all"
    PREFIX_SELECT_CHAT = "select_chat_"
    PREFIX_PREV_SELECT_CHAT_PAGE = "prev_select_chat_page__"
    PREFIX_NEXT_SELECT_CHAT_PAGE = "next_select_chat_page__"
    SELECT_CHAT_PAGE_INFO = "select_chat_page_info"


class UserAndChatsSettingsCallbackData:
    """Класс для хранения callback данных настроек пользователей и чатов"""

    # Commands
    SHOW_MENU = "users_chats_settings_menu"
    RESET_SETTINGS = "reset_settings"
    CONFIRM_RESET = "confirm_reset"
    CANCEL_RESET = "cancel_reset"
    FIRST_TIME_SETTINGS = "first_time_settings"
    CONTINUE_SETTINGS = "continue_settings"
    # First-time work hours
    FIRST_TIME_CHANGE_WORK_START = "first_time_change_work_start"
    FIRST_TIME_CHANGE_WORK_END = "first_time_change_work_end"
    FIRST_TIME_CHANGE_TOLERANCE = "first_time_change_tolerance"
    FIRST_TIME_CHANGE_BREAKS_TIME = "first_time_change_breaks_time"
    FIRST_TIME_SAVE_AND_FINISH = "first_time_save_and_finish"
    FIRST_TIME_CANCEL_TIME_INPUT = "first_time_cancel_time_input"


class BotSettingsCallbackData:
    """Класс для хранения callback данных настроек бота"""

    # Commands
    SHOW_MENU = "bot_settings_menu"


class RootCallbackData:
    """Класс для хранения callback данных root"""

    # Commands
    SHOW_MENU = "root_menu"


class HelpCallbackData:
    """Класс для хранения callback данных помощи"""

    # Commands
    SHOW_MENU = "help_menu"


class NewsCallbackData:
    """Класс для хранения callback данных новостей"""

    # Commands
    SHOW_MENU = "news_menu"


class TemplatesCallbackData:
    """Класс для хранения callback данных шаблонов"""

    # Commands
    SHOW_MENU = "templates_menu"


class CallbackData:
    """Класс для хранения callback данных"""

    Chat = ChatCallbackData
    Report = ReportCallbackData
    User = UserCallbackData
    Menu = MenuCallbackData
    Moderation = ModerationCallbackData
    AdminLogs = AdminLogsCallbackData
    ReleaseNotes = ReleaseNotesCallbackData
    Roles = RoleCallbackData
    Analytics = AnalyticsCallbackData
    Messages = MessagesCallbackData
    UserAndChatsSettings = UserAndChatsSettingsCallbackData
    BotSettings = BotSettingsCallbackData
    Root = RootCallbackData
    Help = HelpCallbackData
    News = NewsCallbackData
    Templates = TemplatesCallbackData
