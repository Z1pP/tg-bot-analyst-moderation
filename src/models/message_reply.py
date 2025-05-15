from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql.schema import Index

from .base import BaseModel


class MessageReply(BaseModel):
    __tablename__ = "message_replies"

    chat_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_sessions.id"),
        nullable=False,
    )
    # Ссылка на сообщение на которое ответили
    original_message_url: Mapped[int] = mapped_column(
        String,
        nullable=False,
    )
    # Сообщение которым ответили
    reply_message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_messages.id"),
        nullable=False,
    )

    reply_user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )
    # Время ответа на сообщение
    response_time_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    __table_args__ = (Index("idx_reply_time", "created_at"),)
