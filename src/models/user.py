from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Index, String
from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from constants.enums import UserRole

from .associations import admin_user_tracking
from .base import BaseModel

if TYPE_CHECKING:
    from .admin_chat_access import AdminChatAccess
    from .message import ChatMessage
    from .message_templates import MessageTemplate
    from .reaction import MessageReaction


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

    chat_access: Mapped[list["AdminChatAccess"]] = relationship(
        "AdminChatAccess",
        back_populates="admin",
    )
    message_templates: Mapped[list["MessageTemplate"]] = relationship(
        "MessageTemplate",
        back_populates="author",
    )
    reactions: Mapped[list["MessageReaction"]] = relationship(
        "MessageReaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    tracked_users: Mapped[list["User"]] = relationship(
        "User",
        secondary=admin_user_tracking,
        primaryjoin="User.id == admin_user_tracking.c.admin_id",
        secondaryjoin="User.id == admin_user_tracking.c.tracked_user_id",
        back_populates="tracking_admins",
    )

    tracking_admins: Mapped[list["User"]] = relationship(
        "User",
        secondary=admin_user_tracking,
        primaryjoin="User.id == admin_user_tracking.c.tracked_user_id",
        secondaryjoin="User.id == admin_user_tracking.c.admin_id",
        back_populates="tracked_users",
    )

    __table_args__ = (
        Index("idx_user_role", "role"),
        Index("idx_user_tg_id", "tg_id"),
        Index("idx_user_is_active", "is_active"),
        Index("idx_user_role_active", "role", "is_active"),
    )
