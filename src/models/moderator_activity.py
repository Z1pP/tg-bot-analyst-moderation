from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

if TYPE_CHECKING:
    from .message import ChatMessage
    from .user import User


from .base import BaseModel


class ModeratorActivity(BaseModel):
    """Модель для отслеживания активности модераторов"""

    __tablename__ = "moderator_activity"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )
    chat_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_sessions.id"),
        nullable=False,
    )
    last_message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_messages.id"),
        nullable=False,
    )
    next_message_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("chat_messages.id"),
        nullable=False,
    )
    inactive_period_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="activities",
    )

    last_message: Mapped["ChatMessage"] = relationship(
        "ChatMessage",
        foreign_keys=[last_message_id],
        back_populates="last_activities",
    )

    next_message: Mapped["ChatMessage"] = relationship(
        "ChatMessage",
        foreign_keys=[next_message_id],
        back_populates="next_activities",
    )

    __table_args__ = (
        Index("idx_activity_moderator", "user_id"),
        Index("idx_activity_period", "inactive_period_seconds"),
    )
