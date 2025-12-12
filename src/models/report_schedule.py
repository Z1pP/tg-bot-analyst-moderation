from datetime import datetime, time

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel


class ReportSchedule(BaseModel):
    __tablename__ = "report_schedules"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE")
    )
    timezone: Mapped[str] = mapped_column(String(length=64))  # Europe/Moscow
    sent_time: Mapped[time] = mapped_column(Time)
    enabled: Mapped[Boolean] = mapped_column(Boolean, default=True)
    next_run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_run_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    __table_args__ = (
        Index("idx_schedule_due", "enabled", "next_run_at"),
        Index("idx_schedule_user_chat", "user_id", "chat_id", unique=True),
    )
