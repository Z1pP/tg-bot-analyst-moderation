from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .admin_chat_access import AdminChatAccess
    from .message import ChatMessage
    from .message_reply import MessageReply
    from .message_templates import MessageTemplate
    from .reaction import MessageReaction


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
