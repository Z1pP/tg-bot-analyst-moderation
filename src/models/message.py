import enum
from typing import TYPE_CHECKING

from aiogram.enums import ContentType
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel

if TYPE_CHECKING:
    from .chat_session import ChatSession
    from .user import User
from sqlalchemy.orm import relationship


class MessageType(str, enum.Enum):
    """Типы сообщений"""

    MESSAGE = "message"
    REPLY = "reply"


class ChatMessage(BaseModel):
    __tablename__ = "chat_messages"

    # Из какого чата сообщение пришло
    chat_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_sessions.id"),
        nullable=False,
    )
    # Кто отправил сообщение
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    # Какое сообщение было отправлено
    message_id: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    # Какой тип сообщения reply или обычное
    message_type: Mapped[str] = mapped_column(
        String(length=32),
        nullable=False,
        default=MessageType.MESSAGE.value,
    )
    # Текст сообщения
    text: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )
    content_type: Mapped[str] = mapped_column(
        String(length=32),
        nullable=False,
        default=ContentType.TEXT.value,
    )

    # Relationships
    chat_session: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="messages",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="messages",
    )

    __table_args__ = (
        Index("idx_message_user", "user_id"),
        Index("idx_message_chat", "chat_id"),
        Index("idx_message_created", "created_at"),
    )
