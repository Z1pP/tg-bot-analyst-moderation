from sqlalchemy import ForeignKey, Index, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel


class AdminChatAccess(BaseModel):
    """Модель для хранения доступа администраторов к чатам"""

    __tablename__ = "admin_chat_access"

    admin_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    chat_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey(
            "chat_sessions.id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )
    # Флаг, указывающий, является ли чат источником статистики
    is_source: Mapped[bool] = mapped_column(default=True)
    # Флаг, указывающий, является ли чат получателем отчетов
    is_target: Mapped[bool] = mapped_column(default=False)

    # Relationships
    admin = relationship("User", back_populates="chat_access")
    chat = relationship("ChatSession", back_populates="admin_access")

    __table_args__ = (
        Index("idx_admin_chat_access_admin_chat", "admin_id", "chat_id", unique=True),
    )
