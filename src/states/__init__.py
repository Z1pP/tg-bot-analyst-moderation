from aiogram.fsm.state import State, StatesGroup


class AddModeratorState(StatesGroup):
    waiting_for_username = State()


class RemoveModeratorState(StatesGroup):
    waiting_for_username = State()
