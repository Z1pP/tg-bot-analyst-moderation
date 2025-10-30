from aiogram.fsm.state import StatesGroup, State


class MessageManager(StatesGroup):
    input_message_link = State()
