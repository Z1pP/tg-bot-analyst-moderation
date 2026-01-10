from typing import TYPE_CHECKING, Optional

from sqlalchemy import ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from constants.work_time import END_TIME, START_TIME, TOLERANCE

from .base import BaseModel

if TYPE_CHECKING:
    from .admin_chat_access import AdminChatAccess
    from .chat_settings import ChatSettings
    from .message import ChatMessage
    from .message_reply import MessageReply
    from .message_templates import MessageTemplate
    from .reaction import MessageReaction
    from .user_chat_status import UserChatStatus


class ChatSession(BaseModel):
    __tablename__ = "chat_sessions"

    chat_id: Mapped[str] = mapped_column(
        String(length=32),
        unique=True,
        nullable=False,
        doc="ID of the chat in Telegram.",
    )

    title: Mapped[str] = mapped_column(
        String(),
        nullable=True,
        doc="Title of the chat.",
    )

    archive_chat_id: Mapped[Optional[str]] = mapped_column(
        String(length=32),
        ForeignKey("chat_sessions.chat_id", ondelete="SET NULL"),
        nullable=True,
        doc="ID of the chat to which moderation reports are sent.",
    )

    # Relationships
    messages: Mapped[list["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="chat_session",
    )

    replies: Mapped[list["MessageReply"]] = relationship(
        "MessageReply",
        back_populates="chat_session",
    )

    admin_access: Mapped[list["AdminChatAccess"]] = relationship(
        "AdminChatAccess",
        back_populates="chat",
    )

    templates: Mapped[list["MessageTemplate"]] = relationship(
        "MessageTemplate",
        back_populates="chat",
    )
    reactions: Mapped[list["MessageReaction"]] = relationship(
        "MessageReaction",
        back_populates="chat",
        cascade="all, delete-orphan",
    )

    user_statuses: Mapped[list["UserChatStatus"]] = relationship(
        "UserChatStatus",
        back_populates="chat",
        cascade="all, delete-orphan",
    )

    archive_chat: Mapped[Optional["ChatSession"]] = relationship(
        "ChatSession",
        remote_side=[chat_id],
        back_populates="linked_work_chats",
        foreign_keys=[archive_chat_id],
    )

    linked_work_chats: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="archive_chat",
        foreign_keys=[archive_chat_id],
    )

    settings: Mapped["ChatSettings"] = relationship(
        "ChatSettings",
        back_populates="chat",
        uselist=False,  # Указываем, что это связь 1-к-1
        cascade="all, delete-orphan",
    )

    @property
    def is_antibot_enabled(self) -> bool:
        return self.settings.is_antibot_enabled if self.settings else False

    @property
    def start_time(self):
        return self.settings.start_time if self.settings else START_TIME

    @property
    def end_time(self):
        return self.settings.end_time if self.settings else END_TIME

    @property
    def tolerance(self) -> int:
        return self.settings.tolerance if self.settings else TOLERANCE

    @property
    def welcome_text(self) -> Optional[str]:
        return self.settings.welcome_text if self.settings else None

    __table_args__ = (
        Index("idx_chat_session_chat_id", "chat_id"),
        Index("idx_chat_session_title", "title"),
    )
