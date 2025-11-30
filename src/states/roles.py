from aiogram.fsm.state import State, StatesGroup


class RoleState(StatesGroup):
    menu = State()
    waiting_user_input = State()
