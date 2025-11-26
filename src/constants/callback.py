class ChatCallbackData:
    """Класс для хранения callback данных чата"""

    # Commands
    ADD = "add_chat"
    REMOVE = "remove_chat"
    GET_STATISTICS = "get_chat_statistics"
    GET_DAILY_RATING = "get_chat_daily_rating"
    SELECT_CHAT = "select_chat"
    ARCHIVE_SETTING = "archive_setting"
    BACK_TO_CHATS_MANAGEMENT = "back_to_chats_management"
    BACK_TO_MAIN_MENU_FROM_CHATS = "back_to_main_menu_from_chats"
    BACK_TO_CHAT_ACTIONS = "back_to_chat_actions"
    ALL_CHATS = "chat__all"
    CHATS_PAGE_INFO = "chats_page_info"
    REMOVE_CHATS_PAGE_INFO = "remove_chats_page_info"

    # Prefixes
    PREFIX_CHAT = "chat__"
    PREFIX_UNTRACK_CHAT = "untrack_chat__"
    PREFIX_CONFIRM_REMOVE_CHAT = "conf_remove_chat__"
    PREFIX_TEMPLATE_SCOPE = "template_scope__"
    PREFIX_PREV_CHATS_PAGE = "prev_chats_page__"
    PREFIX_NEXT_CHATS_PAGE = "next_chats_page__"
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
    SELECT_USER = "select_user"
    ADD = "add_user"
    REMOVE = "remove_user"
    USERS_MENU = "users_menu"
    BACK_TO_MAIN_MENU_FROM_USERS = "back_to_main_menu_from_users"
    CANCEL_ADD = "cancel_add_user"
    ALL_USERS = "all_users"
    USERS_PAGE_INFO = "users_page_info"
    REMOVE_USERS_PAGE_INFO = "remove_users_page_info"

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
    USERS_MENU = "users_menu"
    CHATS_MENU = "chats_menu"
    MESSAGE_MANAGEMENT = "message_management"
    LOCK_MENU = "lock_menu"
    ADMIN_LOGS = "admin_logs"
    MAIN_MENU = "main_menu"
    RELEASE_NOTES = "release_notes"


class AdminLogsCallbackData:
    """Класс для хранения callback данных логов администраторов"""

    # Commands
    HIDE_LOGS = "hide_admin_logs"
    MENU = "admin_logs_menu"
    SELECT_ADMIN = "admin_logs_select_admin"


class ReleaseNotesCallbackData:
    """Класс для хранения callback данных релизных заметок"""

    # Commands
    MENU = "release_notes_menu"
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
    SAVE_NOTE = "save_release_note"

    # Prefixes
    PREFIX_SELECT = "release_note__"
    PREFIX_PREV_PAGE = "prev_release_notes_page__"
    PREFIX_NEXT_PAGE = "next_release_notes_page__"
    PREFIX_CONFIRM_DELETE = "conf_delete_release_note__"
    PREFIX_CONFIRM_BROADCAST = "conf_broadcast_release_note__"
    PREFIX_SELECT_LANGUAGE = "select_language__"
    PREFIX_SELECT_ADD_LANGUAGE = "select_add_language__"


class PermissionsCallbackData:
    """Класс для хранения callback данных управления доступом"""

    # Commands
    MENU = "permissions_menu"


class RoleCallbackData:
    """Класс для хранения callback данных ролей"""

    # Commands
    INPUT_USER_DATA = "input_user_data"
    SELECT_ROLE = "select_role"
    ADD_ROLE = "add_role"
    REMOVE_ROLE = "remove_role"
    ROLES_MENU = "roles_menu"
    BACK_TO_MAIN_MENU_FROM_ROLES = "back_to_main_menu_from_roles"


class CallbackData:
    """Класс для хранения callback данных"""

    Chat = ChatCallbackData
    Report = ReportCallbackData
    User = UserCallbackData
    Menu = MenuCallbackData
    AdminLogs = AdminLogsCallbackData
    ReleaseNotes = ReleaseNotesCallbackData
    Permissions = PermissionsCallbackData
    Role = RoleCallbackData
