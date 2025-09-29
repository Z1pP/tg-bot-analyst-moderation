from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .chat_session import ChatSession
    from .user import User


class UserChatStatus(BaseModel):
    __tablename__ = "user_chat_status"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_banned: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    banned_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )
    is_muted: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )
    muted_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="chat_statuses",
    )
    chat: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="user_statuses",
    )
