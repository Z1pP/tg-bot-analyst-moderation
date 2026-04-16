from pydantic import BaseModel, ConfigDict

from constants.enums import MembershipEventType


class RecordChatMembershipEventDTO(BaseModel):
    """Данные для записи события вступления или ухода из чата."""

    chat_tgid: str
    user_tgid: int
    event_type: MembershipEventType

    model_config = ConfigDict(frozen=True)
