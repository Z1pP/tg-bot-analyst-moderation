from aiogram.fsm.state import State, StatesGroup


class FirstTimeSetupStates(StatesGroup):
    waiting_chat_bound = State()  # шаг 1: ждём привязку чата (/track) или выбор чата
    waiting_user_added = State()  # шаг 2: добавить пользователя
    waiting_work_start = State()  # шаг 3: меню настройки времени (текст + кнопки)
    waiting_work_start_input = State()
    waiting_work_end_input = State()
    waiting_tolerance_input = State()
    waiting_breaks_time_input = State()
    waiting_confirm = State()  # шаг 7: подтверждение настроек
