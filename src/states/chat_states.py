from aiogram.fsm.state import State, StatesGroup


class ChatStateManager(StatesGroup):
    listing_chats = State()
    selecting_chat = State()
    selecting_all_chats = State()
    selecting_period = State()
