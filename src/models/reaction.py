from typing import TYPE_CHECKING

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from constants.enums import ReactionAction

from .base import BaseModel

if TYPE_CHECKING:
    from .chat_session import ChatSession
    from .user import User


class MessageReaction(BaseModel):
    __tablename__ = "message_reactions"

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    message_id: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    action: Mapped["ReactionAction"] = mapped_column(
        SQLAlchemyEnum(ReactionAction),
        nullable=False,
    )
    emoji: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
    )
    message_url: Mapped[str] = mapped_column(
        Text,
        nullable=True,
    )

    # Relationships
    chat: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="reactions",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="reactions",
    )

    __table_args__ = (
        Index("idx_reaction_chat_message", "chat_id", "message_id"),
        Index("idx_reaction_user", "user_id"),
        Index("idx_reaction_created_at", "created_at"),
    )
