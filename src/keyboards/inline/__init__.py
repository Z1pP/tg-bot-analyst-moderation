from .analytics import analytics_menu_ikb
from .calendar_kb import CalendarKeyboard
from .menu import main_menu_ikb
from .punishments import (
    punishment_action_ikb,
    punishment_next_step_ikb,
    punishment_setting_ikb,
)
from .report import (
    order_details_kb_all_users,
    order_details_kb_chat,
    order_details_kb_single_user,
)
from .roles import role_select_ikb
from .time_period import (
    time_period_ikb_all_users,
    time_period_ikb_chat,
    time_period_ikb_single_user,
)
from .users import (
    all_users_actions_ikb,
    back_to_users_menu_ikb,
    remove_user_inline_kb,
    user_actions_ikb,
    users_menu_ikb,
)

__all__ = [
    "main_menu_ikb",
    "remove_user_inline_kb",
    "users_menu_ikb",
    "back_to_users_menu_ikb",
    "user_actions_ikb",
    "all_users_actions_ikb",
    "order_details_kb_single_user",
    "order_details_kb_all_users",
    "order_details_kb_chat",
    "time_period_ikb",
    "time_period_ikb_single_user",
    "time_period_ikb_all_users",
    "time_period_ikb_chat",
    "CalendarKeyboard",
    "role_select_ikb",
    "punishment_setting_ikb",
    "punishment_action_ikb",
    "punishment_next_step_ikb",
    "analytics_menu_ikb",
]
