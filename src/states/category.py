from aiogram.fsm.state import State, StatesGroup


class CategoryStateManager(StatesGroup):
    process_category_name = State()
    confirm_category_creation = State()
    removing_category = State()
    confirm_category_edit = State()
