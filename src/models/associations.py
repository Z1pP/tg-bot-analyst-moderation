from sqlalchemy import Column, ForeignKey, Integer, Table

from .base import Base

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
)
