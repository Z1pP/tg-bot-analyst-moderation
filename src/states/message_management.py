from aiogram.fsm.state import State, StatesGroup


class MessageManagerState(StatesGroup):
    """Состояния для работы с сообщениями через управлениями сообщенями."""

    waiting_message_link = State()
    waiting_action_select = State()
    waiting_delete_confirm = State()
    waiting_reply_message = State()
