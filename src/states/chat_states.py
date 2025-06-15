from aiogram.fsm.state import State, StatesGroup


class ChatStateManager(StatesGroup):
    report_menu = State()

    listing_chats = State()
    listing_tracking_chats = State()

    selecting_chat = State()
    selecting_all_chats = State()

    selecting_period = State()
    selecting_custom_period = State()
