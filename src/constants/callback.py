class ChatCallbackData:
    """Класс для хранения callback данных чата"""

    # Commands
    ADD = "add_chat"
    REMOVE = "remove_chat"
    GET_REPORT = "get_chat_report"
    GET_DAILY_RATING = "get_chat_daily_rating"
    GET_STATISTICS = "get_chat_statistics"
    CHATS_MENU = "chats_menu"
    BACK_TO_MAIN_MENU = "back_to_main_menu_from_chats"
    SELECT_ANOTHER_CHAT = "select_another_chat"

    # Prefixes
    PREFIX_UNTRACK_CHAT = "untrack_chat__"
    PREFIX_CONFIRM_REMOVE_CHAT = "confirm_remove_chat__"


class CallbackData:
    """Класс для хранения callback данных"""

    Chat = ChatCallbackData()
