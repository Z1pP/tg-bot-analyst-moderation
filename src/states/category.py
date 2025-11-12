from aiogram.fsm.state import State, StatesGroup


class CategoryStateManager(StatesGroup):
    process_category_name = State()
    confirm_category_creation = State()
    editing_category_name = State()
    removing_category = State()
