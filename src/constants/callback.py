class ChatCallbackData:
    """Класс для хранения callback данных чата"""

    # Commands
    ADD = "add_chat"
    REMOVE = "remove_chat"
    GET_REPORT = "get_chat_report"
    GET_DAILY_RATING = "get_chat_daily_rating"
    GET_STATISTICS = "get_chat_statistics"
    CHATS_MENU = "chats_menu"
    BACK_TO_MAIN_MENU_FROM_CHATS = "back_to_main_menu_from_chats"
    SELECT_ANOTHER_CHAT = "select_another_chat"
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


class CallbackData:
    """Класс для хранения callback данных"""

    Chat = ChatCallbackData()
