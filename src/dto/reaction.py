from datetime import datetime
from typing import Optional

from pydantic import BaseModel

from models.reaction import ReactionAction


class MessageReactionDTO(BaseModel):
    chat_tgid: str
    user_tgid: str
    message_id: str
    action: ReactionAction
    emoji: str
    message_url: str
    created_at: Optional[datetime] = None
