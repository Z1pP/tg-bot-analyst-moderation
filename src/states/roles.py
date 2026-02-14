from aiogram.fsm.state import State, StatesGroup


class RoleState(StatesGroup):
    waiting_user_input = State()
