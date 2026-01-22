from datetime import time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .chat_session import ChatSession


class ChatSettings(BaseModel):
    __tablename__ = "chat_settings"

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        doc="ID of the chat in the database.",
    )

    start_time: Mapped[time] = mapped_column(
        Time,
        nullable=True,
        doc="Start work time for report filtering. Default is None.",
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        nullable=True,
        doc="End work time for report filtering. Default is None.",
    )

    tolerance: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        doc="Tolerance for report filtering. Default is None.",
    )

    breaks_time: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        doc="Breaks time for report filtering. Default is None.",
    )

    is_antibot_enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
        doc="Whether antibot verification is enabled for this chat.",
    )

    welcome_text: Mapped[Optional[str]] = mapped_column(
        String(length=4096),  # Maximum message length in TG
        nullable=True,
        doc="Custom welcome message for new members.",
    )

    # Relationships
    chat: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="settings",
    )
