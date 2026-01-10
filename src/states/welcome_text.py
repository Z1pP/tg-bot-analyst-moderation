from aiogram.fsm.state import State, StatesGroup


class WelcomeTextState(StatesGroup):
    waiting_welcome_text_input = State()
