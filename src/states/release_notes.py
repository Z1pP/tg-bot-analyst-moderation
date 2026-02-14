from aiogram.fsm.state import State, StatesGroup


class ReleaseNotesStateManager(StatesGroup):
    """Состояния сценария рассылки релизной заметки (ввод текста → язык → подтверждение)."""

    waiting_for_note_text = State()
    selecting_broadcast_language = State()
    confirming_broadcast = State()
