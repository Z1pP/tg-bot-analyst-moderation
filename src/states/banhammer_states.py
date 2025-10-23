from aiogram.fsm.state import State, StatesGroup


class BanHammerStates(StatesGroup):
    block_menu = State()


class AmnestyStates(StatesGroup):
    waiting_user_input = State()
    waiting_chat_select = State()
    waiting_confirmation_action = State()
    waiting_action_select = State()


class BanUserStates(StatesGroup):
    waiting_user_input = State()
    waiting_reason_input = State()
    waiting_chat_select = State()
    waiting_confirmation_action = State()
