from sqlalchemy import Column, DateTime, ForeignKey, Integer, Table

from .base import Base, get_current_time

admin_user_tracking = Table(
    "admin_user_tracking",
    Base.metadata,
    Column(
        "admin_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "tracked_user_id",
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "created_at",
        DateTime(timezone=True),
        default=get_current_time,
        nullable=False,
    ),
)
