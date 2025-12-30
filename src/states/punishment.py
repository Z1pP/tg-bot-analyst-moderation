from aiogram.fsm.state import State, StatesGroup


class PunishmentState(StatesGroup):
    """Состояния для настройки лестницы наказаний"""

    waiting_for_action_type = State()  # Ожидание выбора типа (Warn, Mute, Ban)
    waiting_for_duration = State()  # Ожидание ввода времени (для Mute)
    confirm_save = State()  # Ожидание подтверждения сохранения всей лестницы
