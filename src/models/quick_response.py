from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .quick_response import QuickResponse
    from .user import User


class QuickResponse(BaseModel):
    __tablename__ = "quick_responses"

    title: Mapped[str] = mapped_column(
        String,
        nullable=False,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quick_response_categories.id"),
        nullable=True,
        index=True,
    )
    author_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )
    usage_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Relationships
    author: Mapped["User"] = relationship(
        "User",
        back_populates="quick_responses",
    )
    category: Mapped["QuickResponseCategory"] = relationship(
        "QuickResponseCategory",
        back_populates="responses",
    )


class QuickResponseCategory(BaseModel):
    __tablename__ = "quick_response_categories"

    name: Mapped[str] = mapped_column(
        String,
        unique=True,
        nullable=False,
        index=True,
    )
    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    # Relationships
    responses: Mapped[list["QuickResponse"]] = relationship(
        "QuickResponse",
        back_populates="category",
    )
