from aiogram.fsm.state import State, StatesGroup


class UsernameStates(StatesGroup):
    """Состояние для задавания имени пользователя"""

    waiting_add_user_data_input = State()
    waiting_remove_user_data_input = State()


class SingleUserReportStates(StatesGroup):
    selected_single_user = State()
    selecting_period = State()
    selecting_custom_period = State()


class AllUsersReportStates(StatesGroup):
    selected_all_users = State()
    selecting_period = State()
    selecting_custom_period = State()


class UserStateManager(StatesGroup):
    """Состояния для управления пользователями через inline клавиатуру"""

    users_menu = State()
    removing_user = State()
