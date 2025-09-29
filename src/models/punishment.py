from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from constants.punishment import PunishmentType

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class Punishment(BaseModel):
    __tablename__ = "punishments"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    step: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    punishment_type: Mapped[Enum] = mapped_column(
        SQLAlchemyEnum(PunishmentType),
        nullable=False,
    )
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
    punished_by_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    chat_id: Mapped[str] = mapped_column(
        String(length=32),
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="punishments",
    )
    punished_by: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[punished_by_id],
    )
