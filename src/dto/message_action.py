from typing import Optional

from pydantic import BaseModel, ConfigDict


class MessageActionDTO(BaseModel):
    """DTO для действий с сообщениями через админ-панель."""

    chat_tgid: str
    message_id: int
    admin_tgid: str
    admin_username: str
    admin_message_id: Optional[int] = None

    model_config = ConfigDict(frozen=True)


class SendMessageDTO(BaseModel):
    """DTO для отправки сообщения в чат."""

    chat_tgid: str
    admin_tgid: str
    admin_username: str
    admin_message_id: int

    model_config = ConfigDict(frozen=True)
