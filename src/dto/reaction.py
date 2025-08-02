from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from models.reaction import ReactionAction


@dataclass
class MessageReactionDTO:
    chat_id: int
    user_id: int
    message_id: str
    action: ReactionAction
    emoji: str
    message_url: str
    created_at: Optional[datetime] = None
