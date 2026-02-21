from dataclasses import dataclass
from typing import Any, Optional

from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# Ключи данных FSM для сценария управления сообщениями (избегаем magic-строк).
ACTIVE_MESSAGE_ID = "active_message_id"
BROADCAST_ALL = "broadcast_all"
CHAT_TGID = "chat_tgid"
CHATNAME = "chatname"
ADMIN_TGID = "admin_tgid"
ADMIN_USERNAME = "admin_username"
ADMIN_MESSAGE_ID = "admin_message_id"
MESSAGE_ID = "message_id"  # tg_message_id в контексте действия с сообщением


class MessageManagerState(StatesGroup):
    """Состояния для работы с сообщениями через управлениями сообщенями."""

    waiting_message_link = State()
    waiting_action_select = State()
    waiting_confirm = State()
    waiting_reply_message = State()
    waiting_select_chat = State()
    waiting_content = State()
    waiting_confirm_send = State()


@dataclass(frozen=True)
class MessageActionStateData:
    """Данные state для действия с конкретным сообщением (удалить/ответить)."""

    chat_tgid: str
    message_id: int
    active_message_id: int


@dataclass(frozen=True)
class SendConfirmStateData:
    """Данные state для подтверждения отправки (один чат или рассылка)."""

    active_message_id: int
    broadcast_all: bool
    chat_tgid: Optional[str]
    chatname: str
    admin_tgid: str
    admin_username: str
    admin_message_id: int


async def get_message_action_state(
    state: FSMContext,
) -> Optional[MessageActionStateData]:
    """Извлекает типизированные данные действия с сообщением из FSM."""
    data: dict[str, Any] = await state.get_data()
    chat_tgid = data.get(CHAT_TGID)
    message_id = data.get(MESSAGE_ID)
    active_message_id = data.get(ACTIVE_MESSAGE_ID)
    if not chat_tgid or message_id is None or not active_message_id:
        return None
    return MessageActionStateData(
        chat_tgid=chat_tgid,
        message_id=int(message_id),
        active_message_id=int(active_message_id),
    )


async def get_send_confirm_state(state: FSMContext) -> Optional[SendConfirmStateData]:
    """Извлекает типизированные данные подтверждения отправки из FSM."""
    data: dict[str, Any] = await state.get_data()
    active_message_id = data.get(ACTIVE_MESSAGE_ID)
    admin_tgid = data.get(ADMIN_TGID)
    admin_username = data.get(ADMIN_USERNAME)
    admin_message_id = data.get(ADMIN_MESSAGE_ID)
    if not all((active_message_id, admin_tgid, admin_username, admin_message_id)):
        return None
    return SendConfirmStateData(
        active_message_id=int(active_message_id),
        broadcast_all=bool(data.get(BROADCAST_ALL, False)),
        chat_tgid=data.get(CHAT_TGID),
        chatname=data.get(CHATNAME) or "",
        admin_tgid=str(admin_tgid),
        admin_username=str(admin_username),
        admin_message_id=int(admin_message_id),
    )
