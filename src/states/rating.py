from aiogram.fsm.state import State, StatesGroup


class RatingStateManager(StatesGroup):
    selecting_period = State()
    selecting_custom_period = State()
