from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional

from models import ChatMessage, MessageReply

from .chat import ChatDTO
from .user import UserDTO


class MessageType(Enum):
    """Типы сообщений"""

    MESSAGE = "message"
    REPLY = "reply"


@dataclass
class MessageDTO:
    """Data Transfer Object для сообщения"""

    # Обязательные поля
    id: int
    chat_id: int
    user_id: int
    message_id: str
    message_type: str
    created_at: datetime

    # Опциональные поля
    text: Optional[str] = None
    reply_to_message_id: Optional[str] = None

    # Связанные объекты
    user: Optional[UserDTO] = None
    chat: Optional[ChatDTO] = None

    @classmethod
    def from_entity(cls, message: "ChatMessage") -> "MessageDTO":
        """
        Создает DTO из модели ChatMessage

        Args:
            message: Модель сообщения

        Returns:
            MessageDTO: DTO сообщения
        """
        return cls(
            id=message.id,
            chat_id=message.chat_id,
            user_id=message.user_id,
            message_id=message.message_id,
            message_type=message.message_type,
            text=message.text,
            created_at=message.created_at,
            user=UserDTO.from_entity(message.user) if message.user else None,
            chat=ChatDTO.from_entity(message.chat_session)
            if message.chat_session
            else None,
        )

    def to_dict(self) -> dict:
        """
        Преобразует DTO в словарь

        Returns:
            dict: Словарь с данными сообщения
        """
        return {
            "id": self.id,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "message_id": self.message_id,
            "message_type": self.message_type,
            "text": self.text,
            "created_at": self.created_at.isoformat(),
            "reply_to_message_id": self.reply_to_message_id,
            "user": self.user.to_dict() if self.user else None,
            "chat": self.chat.to_dict() if self.chat else None,
        }


@dataclass
class CreateMessageDTO:
    """DTO для создания нового сообщения"""

    chat_id: int
    user_id: int
    message_id: str
    message_type: str
    text: Optional[str] = None
    reply_to_message_id: Optional[str] = None


@dataclass
class MessageReplyDTO:
    """DTO для связи сообщений reply"""

    id: int
    original_message_id: int
    reply_message_id: int
    original_user_id: int
    reply_user_id: int
    response_time_seconds: int
    created_at: datetime

    # Связанные сообщения
    original_message: Optional[MessageDTO] = None
    reply_message: Optional[MessageDTO] = None

    @classmethod
    def from_entity(cls, reply: "MessageReply") -> "MessageReplyDTO":
        """
        Создает DTO из модели MessageReply

        Args:
            reply: Модель связи сообщений

        Returns:
            MessageReplyDTO: DTO связи сообщений
        """
        return cls(
            id=reply.id,
            original_message_id=reply.original_message_id,
            reply_message_id=reply.reply_message_id,
            original_user_id=reply.original_user_id,
            reply_user_id=reply.reply_user_id,
            response_time_seconds=reply.response_time_seconds,
            created_at=reply.created_at,
            original_message=MessageDTO.from_entity(reply.original_message)
            if reply.original_message
            else None,
            reply_message=MessageDTO.from_entity(reply.reply_message)
            if reply.reply_message
            else None,
        )

    def to_dict(self) -> dict:
        """
        Преобразует DTO в словарь

        Returns:
            dict: Словарь с данными связи сообщений
        """
        return {
            "id": self.id,
            "original_message_id": self.original_message_id,
            "reply_message_id": self.reply_message_id,
            "original_user_id": self.original_user_id,
            "reply_user_id": self.reply_user_id,
            "response_time_seconds": self.response_time_seconds,
            "created_at": self.created_at.isoformat(),
            "original_message": self.original_message.to_dict()
            if self.original_message
            else None,
            "reply_message": self.reply_message.to_dict()
            if self.reply_message
            else None,
        }


@dataclass
class CreateMessageReplyDTO:
    """DTO для создания новой связи сообщений"""

    original_message_id: int
    reply_message_id: int
    original_user_id: int
    reply_user_id: int
