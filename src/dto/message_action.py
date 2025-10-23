from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True, slots=True)
class MessageActionDTO:
    """DTO для действий с сообщениями через админ-панель."""

    chat_tgid: str
    message_id: int
    admin_tgid: str
    admin_username: str
    admin_message_id: Optional[int] = None
