from aiogram.fsm.state import State, StatesGroup


class UserStateManager(StatesGroup):
    """Состояния для управления пользователями."""

    selecting_user = State()
    viewing_user = State()
    editing_user = State()

    # Состояния для работы с отчетами для выбранного пользователя
    report_menu = State()
    process_select_time_period = State()
    report_full_selecting_period = State()

    process_custom_period_input = State()
    report_full_waiting_input_period = State()


class UsernameManagement(StatesGroup):
    """Состояние для задавания имени пользователя"""

    imput_username = State()
