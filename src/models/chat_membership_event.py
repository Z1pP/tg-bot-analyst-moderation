from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from constants.enums import MembershipEventType

from .base import BaseModel

if TYPE_CHECKING:
    from .chat_session import ChatSession


class ChatMembershipEvent(BaseModel):
    """Событие вступления или ухода участника из отслеживаемого чата."""

    __tablename__ = "chat_membership_events"

    chat_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
    )
    user_tgid: Mapped[int] = mapped_column(BigInteger, nullable=False)
    event_type: Mapped[str] = mapped_column(
        String(16),
        nullable=False,
    )

    chat: Mapped["ChatSession"] = relationship(
        "ChatSession",
        back_populates="membership_events",
    )

    __table_args__ = (
        Index(
            "idx_chat_membership_events_chat_created",
            "chat_id",
            "created_at",
        ),
    )

    @property
    def event_kind(self) -> MembershipEventType:
        return MembershipEventType(self.event_type)
