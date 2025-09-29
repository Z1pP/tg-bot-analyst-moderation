from typing import TYPE_CHECKING, Optional

from sqlalchemy import Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .admin_chat_access import AdminChatAccess
    from .message import ChatMessage
    from .message_reply import MessageReply
    from .message_templates import MessageTemplate
    from .reaction import MessageReaction
    from .user_chat_status import UserChatStatus


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

    archive_chat_id: Mapped[Optional[str]] = mapped_column(
        String(length=32),
        nullable=True,
        doc="ID of the chat to which moderation reports are sent.",
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

    admin_access: Mapped[list["AdminChatAccess"]] = relationship(
        "AdminChatAccess",
        back_populates="chat",
    )

    templates: Mapped[list["MessageTemplate"]] = relationship(
        "MessageTemplate",
        back_populates="chat",
    )
    reactions: Mapped[list["MessageReaction"]] = relationship(
        "MessageReaction",
        back_populates="chat",
        cascade="all, delete-orphan",
    )

    user_statuses: Mapped[list["UserChatStatus"]] = relationship(
        "UserChatStatus",
        back_populates="chat",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_chat_session_chat_id", "chat_id"),
        Index("idx_chat_session_title", "title"),
    )
