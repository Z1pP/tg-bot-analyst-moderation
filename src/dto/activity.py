from dataclasses import dataclass
from datetime import datetime

from models import ModeratorActivity


@dataclass
class CreateActivityDTO:
    user_id: int
    chat_id: int
    last_message_id: int
    next_message_id: int
    inactive_period_seconds: int


@dataclass
class ResultActivityDTO:
    id: int
    user_id: int
    chat_id: int
    last_message_id: int
    next_message_id: int
    inactive_period_seconds: int
    created_at: datetime

    @classmethod
    def from_model(cls, model: ModeratorActivity) -> "ResultActivityDTO":
        return cls(
            id=model.id,
            user_id=model.user_id,
            chat_id=model.chat_id,
            last_message_id=model.last_message_id,
            next_message_id=model.next_message_id,
            inactive_period_seconds=model.inactive_period_seconds,
            created_at=model.created_at,
        )
