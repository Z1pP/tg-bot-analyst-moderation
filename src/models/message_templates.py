from typing import TYPE_CHECKING, List

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import BaseModel

if TYPE_CHECKING:
    from .user import User


class MessageTemplate(BaseModel):
    __tablename__ = "message_templates"

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        unique=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("template_categories.id"),
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
        back_populates="message_templates",
    )
    category: Mapped["TemplateCategory"] = relationship(
        "TemplateCategory",
        back_populates="templates",
    )
    media_items: Mapped[List["TemplateMedia"]] = relationship(
        "TemplateMedia",
        back_populates="template",
        order_by="TemplateMedia.position",
        cascade="all, delete-orphan",
    )


class TemplateCategory(BaseModel):
    __tablename__ = "template_categories"

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
    templates: Mapped[list["MessageTemplate"]] = relationship(
        "MessageTemplate",
        back_populates="category",
    )


class TemplateMedia(BaseModel):
    __tablename__ = "template_media"

    template_id: Mapped[int] = mapped_column(  # Изменено с response_id
        Integer,
        ForeignKey("message_templates.id"),
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
    )
    media_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    position: Mapped[int] = mapped_column(
        Integer,
        default=0,
    )

    # Relationships
    template: Mapped["MessageTemplate"] = relationship(
        "MessageTemplate",
        back_populates="media_items",
    )
