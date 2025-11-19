from aiogram.fsm.state import State, StatesGroup


class ReleaseNotesStateManager(StatesGroup):
    menu = State()
    selecting_language = State()
    selecting_add_language = State()
    waiting_for_title = State()
    waiting_for_content = State()
    view_note = State()
    editing_note = State()
    editing_title = State()
    editing_content = State()
    deleting_note = State()
    broadcasting_note = State()
