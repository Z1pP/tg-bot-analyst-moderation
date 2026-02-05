from aiogram.fsm.state import State, StatesGroup


class AmnestyStates(StatesGroup):
    waiting_user_input = State()
    waiting_chat_select = State()
    waiting_confirmation_action = State()
    waiting_action_select = State()


class BanUserStates(StatesGroup):
    waiting_user_input = State()
    waiting_reason_input = State()
    waiting_chat_select = State()


class WarnUserStates(StatesGroup):
    waiting_user_input = State()
    waiting_reason_input = State()
    waiting_chat_select = State()
