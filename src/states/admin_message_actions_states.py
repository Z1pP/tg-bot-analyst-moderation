from aiogram.fsm.state import State, StatesGroup


class AdminMessageActionsStates(StatesGroup):
    """Состояния для работы с сообщениями через админ-панель."""

    waiting_action_select = State()
    waiting_delete_confirm = State()
    waiting_reply_message = State()
