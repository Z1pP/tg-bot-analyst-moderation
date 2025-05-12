from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .message import ChatMessage


class UserRole(Enum):
    ADMIN = "admin"
    MODERATOR = "moderator"
    USER = "user"


class User(BaseModel):
    __tablename__ = "users"

    tg_id: Mapped[str] = mapped_column(
        String(length=32),
        nullable=True,
        unique=True,
    )
    username: Mapped[str] = mapped_column(
        String(length=64),
        nullable=True,
    )
    role: Mapped[Enum] = mapped_column(
        SQLAlchemyEnum(UserRole),
        nullable=False,
        default=UserRole.MODERATOR,
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    # Realationships
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("idx_user_role", "role"),
        Index("idx_user_tg_id", "tg_id"),
    )
