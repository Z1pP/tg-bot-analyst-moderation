from dataclasses import dataclass
from typing import Optional

from aiogram.enums import ContentType

from .chat import ChatDTO
from .user import UserDTO


@dataclass
class MessageDTO:
    user: UserDTO
    chat: ChatDTO
    message_id: str
    text: str
    message_type: ContentType
    reply_to_message_id: Optional[int] = None
