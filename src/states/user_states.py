from aiogram.fsm.state import State, StatesGroup


class UserManagement(StatesGroup):
    """Состояния для управления пользователями."""

    selecting_user = State()
    viewing_user = State()
    editing_user = State()

    # Состояния для работы с отчетами для выбранного пользователя
    report_menu = State()
    report_daily_selecting_period = State()
    report_avg_selecting_period = State()
    report_response_time_selecting_date = State()

    report_daily_waiting_input_period = State()
    report_avg_waiting_input_period = State()
    report_reponse_time_input_period = State()


class UsernameManagement(StatesGroup):
    """Состояние для задавания имени пользователя"""

    imput_username = State()
