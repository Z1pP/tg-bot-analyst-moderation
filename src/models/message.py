import enum
from typing import TYPE_CHECKING

from aiogram.enums import ContentType
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .chat_session import ChatSession
    from .message_reply import MessageReply
    from .user import User


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

    replies: Mapped[list["MessageReply"]] = relationship(
        "MessageReply",
        foreign_keys="MessageReply.reply_message_id",
        cascade="all, delete-orphan",
        back_populates="reply_message",
    )

    __table_args__ = (
        Index("idx_message_user", "user_id"),
        Index("idx_message_chat", "chat_id"),
        Index("idx_message_created", "created_at"),
        Index("idx_message_chat_created", "chat_id", "created_at"),
        Index("idx_message_user_created", "user_id", "created_at"),
        Index("idx_message_type", "message_type"),
        Index("idx_message_user_type", "user_id", "message_type"),
    )
