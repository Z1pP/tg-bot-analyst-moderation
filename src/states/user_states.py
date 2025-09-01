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


class UsernameStates(StatesGroup):
    """Состояние для задавания имени пользователя"""

    waiting_user_data_input = State()


class SingleUserReportStates(StatesGroup):
    selected_single_user = State()
    selecting_period = State()
    waiting_cutom_period = State()
    order_details_report = State()


class AllUsersReportStates(StatesGroup):
    selected_all_users = State()
    selecting_period = State()
    waiting_custom_period = State()
