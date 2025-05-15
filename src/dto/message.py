from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models import ChatMessage


@dataclass
class CreateMessageDTO:
    """DTO для создания нового сообщения"""

    chat_id: int
    user_id: int
    message_id: str
    message_type: str
    content_type: str
    text: Optional[str] = None
    created_at: Optional[datetime] = None


@dataclass
class ResultMessageDTO:
    """Data Transfer Object для сообщения"""

    # Обязательные поля
    id: int
    db_chat_id: int
    db_user_id: int
    message_id: str
    message_type: str
    content_type: str
    created_at: datetime
    text: Optional[str] = None

    @classmethod
    def from_entity(cls, message: "ChatMessage") -> "ResultMessageDTO":
        """
        Создает DTO из модели ChatMessage

        Args:
            message: Модель сообщения

        Returns:
            MessageDTO: DTO сообщения
        """
        return cls(
            id=message.id,
            db_chat_id=message.chat_id,
            db_user_id=message.user_id,
            message_id=message.message_id,
            message_type=message.message_type,
            content_type=message.content_type,
            text=message.text,
            created_at=message.created_at,
        )
