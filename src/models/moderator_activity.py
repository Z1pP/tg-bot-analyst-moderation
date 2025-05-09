from sqlalchemy import ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class ModeratorActivity(BaseModel):
    """Модель для отслеживания активности модераторов"""

    __tablename__ = "moderator_activity"

    moderator_id: Mapped[int] = mapped_column(
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

    __table_args__ = (
        Index("idx_activity_moderator", "moderator_id"),
        Index("idx_activity_period", "inactive_period_seconds"),
    )
