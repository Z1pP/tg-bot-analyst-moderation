from datetime import time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, ForeignKey, Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from constants.work_time import END_TIME, START_TIME, TOLERANCE

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
        default=START_TIME,
        doc="Start work time for report filtering. Default is global START_TIME.",
    )

    end_time: Mapped[time] = mapped_column(
        Time,
        default=END_TIME,
        doc="End work time for report filtering. Default is global END_TIME.",
    )

    tolerance: Mapped[int] = mapped_column(
        Integer,
        default=TOLERANCE,
        doc="Tolerance for report filtering. Default is global TOLERANCE.",
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
