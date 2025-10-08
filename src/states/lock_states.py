from aiogram.fsm.state import State, StatesGroup


class LockStates(StatesGroup):
    lock_menu = State()
