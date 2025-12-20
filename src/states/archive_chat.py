from aiogram.fsm.state import State, StatesGroup


class ChatArchiveState(StatesGroup):
    waiting_time_input = State()
