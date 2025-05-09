from typing import TYPE_CHECKING

from aiogram.enums import ContentType
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel

if TYPE_CHECKING:
    from .chat_session import ChatSession
    from .user import User
from sqlalchemy.orm import relationship


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
    message_type: Mapped[str] = mapped_column(
        String(length=32),
        nullable=False,
        default=ContentType.TEXT.value,
    )
    # Текст сообщения
    text: Mapped[str] = mapped_column(
        Text,
        nullable=True,
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


class MessageReply(BaseModel):
    __tablename__ = "message_replies"

    original_message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_messages.id"),
        nullable=False,
    )
    reply_message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_messages.id"),
        nullable=False,
    )
    original_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )
    reply_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )
    response_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Relationships
    original_message: Mapped["ChatMessage"] = relationship(
        "ChatMessage",
        foreign_keys=[original_message_id],
    )
    reply_message: Mapped["ChatMessage"] = relationship(
        "ChatMessage",
        foreign_keys=[reply_message_id],
    )

    __table_args__ = (
        Index("idx_reply_original_message", "original_message_id"),
        Index("idx_reply_users", "original_user_id", "reply_user_id"),
        Index("idx_reply_time", "created_at"),
    )
