from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .quick_response import QuickResponse
    from .user import User


class QuickResponse(BaseModel):
    __tablename__ = "quick_responses"

    title: Mapped[str] = mapped_column(
        String(200),
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
    media_items: Mapped[List["QuickResponseMedia"]] = relationship(
        "QuickResponseMedia",
        back_populates="response",
        order_by="QuickResponseMedia.position",
        cascade="all, delete-orphan",
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


class QuickResponseMedia(BaseModel):
    __tablename__ = "quick_response_media"

    response_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("quick_responses.id"),
        nullable=False,
    )
    file_id: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
    )
    file_unique_id: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        unique=True,
    )  # Telegram file_id of the media
    media_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    # Relationships
    response: Mapped["QuickResponse"] = relationship(
        "QuickResponse",
        back_populates="media_items",
    )
