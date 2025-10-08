from sqlalchemy import Enum as SQLAlchemyEnum
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .base import BaseModel
from .punishment import PunishmentType


class PunishmentLadder(BaseModel):
    __tablename__ = "punishment_ladder"

    chat_id: Mapped[str | None] = mapped_column(
        String(length=32),
        nullable=True,
        index=True,
    )
    step: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    punishment_type: Mapped[PunishmentType] = mapped_column(
        SQLAlchemyEnum(PunishmentType, name="punishmenttype"),
        nullable=False,
    )
    duration_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )
