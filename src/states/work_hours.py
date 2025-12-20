from aiogram.fsm.state import State, StatesGroup


class WorkHoursState(StatesGroup):
    """Состояния для настройки времени сбора данных для отчетов"""

    waiting_work_start_input = State()
    waiting_work_end_input = State()
    waiting_tolerance_input = State()

