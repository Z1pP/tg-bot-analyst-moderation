from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models.reaction import ReactionAction


class MessageReactionDTO(BaseModel):
    chat_id: int
    user_id: int
    message_id: str
    action: ReactionAction
    emoji: str
    message_url: str
    created_at: Optional[datetime] = None
