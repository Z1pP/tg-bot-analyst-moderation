from datetime import datetime
from typing import Optional

from pydantic import BaseModel, field_validator

from models import ChatMessage
from models.message import MessageType


class CreateMessageDTO(BaseModel):
    """DTO для создания нового сообщения"""

    chat_tgid: str
    user_tgid: str
    message_id: str
    message_type: str
    content_type: str
    created_at: datetime
    text: Optional[str] = None

    @field_validator("message_type")
    @classmethod
    def validate_message_type(cls, v: str) -> str:
        if v not in [MessageType.MESSAGE.value, MessageType.REPLY.value]:
            raise ValueError("Invalid message type")
        return v


class ResultMessageDTO(CreateMessageDTO):
    """Data Transfer Object для сообщения"""

    # Обязательные поля
    id: int

    @classmethod
    def from_model(cls, message: "ChatMessage") -> "ResultMessageDTO":
        """
        Создает DTO из модели ChatMessage

        Args:
            message: Модель сообщения

        Returns:
            ResultMessageDTO: DTO сообщения
        """
        return cls(
            id=message.id,
            chat_id=message.chat_id,
            user_id=message.user_id,
            message_id=message.message_id,
            message_type=message.message_type,
            content_type=message.content_type.value,
            text=message.text,
            created_at=message.created_at,
        )
