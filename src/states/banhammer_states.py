from aiogram.fsm.state import State, StatesGroup


class BanHammerStates(StatesGroup):
    block_menu = State()


class AmnestyStates(StatesGroup):
    waiting_user_input = State()
    waiting_chat_select = State()
