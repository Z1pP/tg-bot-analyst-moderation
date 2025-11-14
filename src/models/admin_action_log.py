from typing import TYPE_CHECKING, Optional

import sqlalchemy as sa
from sqlalchemy import ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class AdminActionLog(BaseModel):
    __tablename__ = "admin_action_logs"

    admin_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    action_type: Mapped[str] = mapped_column(
        sa.String(length=50),
        nullable=False,
    )
    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Дополнительная информация о действии (пользователь, чат, период и т.д.)",
    )

    # Relationships
    admin: Mapped["User"] = relationship(
        "User",
        back_populates="action_logs",
    )

    __table_args__ = (
        Index("idx_admin_action_log_admin", "admin_id"),
        Index("idx_admin_action_log_type", "action_type"),
        Index("idx_admin_action_log_created", "created_at"),
        Index("idx_admin_action_log_admin_created", "admin_id", "created_at"),
    )
