from aiogram.fsm.state import State, StatesGroup


class ChatStateManager(StatesGroup):
    listing_tracking_chats = State()

    selecting_chat = State()
    selecting_chat_for_report = State()
    selecting_chat_report_action = State()

    selecting_period = State()
    selecting_custom_period = State()
