from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .message import ChatMessage
    from .message_reply import MessageReply


class ChatSession(BaseModel):
    __tablename__ = "chat_sessions"

    chat_id: Mapped[str] = mapped_column(
        String(length=32),
        unique=True,
        nullable=False,
    )
    title: Mapped[str] = mapped_column(
        String(),
        nullable=True,
    )

    # Relationships
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="chat_session",
    )

    replies: Mapped[list["MessageReply"]] = relationship(
        "MessageReply",
        back_populates="chat_session",
    )

    admin_access = relationship("AdminChatAccess", back_populates="chat")
