from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class BufferedMessageDTO(BaseModel):
    """Минималистичный DTO для буферизации сообщений в Redis"""

    chat_id: int
    user_id: int
    message_id: str
    message_type: str
    content_type: str
    text: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BufferedReactionDTO(BaseModel):
    """Минималистичный DTO для буферизации реакций в Redis"""

    chat_id: int
    user_id: int
    message_id: str
    action: str  # ReactionAction enum value
    emoji: str
    message_url: str
    created_at: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)


class BufferedMessageReplyDTO(BaseModel):
    """Минималистичный DTO для буферизации reply сообщений в Redis"""

    chat_id: int
    original_message_url: str
    reply_message_id_str: str  # Telegram message_id (строка), не DB id
    reply_user_id: int
    response_time_seconds: int
    created_at: datetime

    model_config = ConfigDict(arbitrary_types_allowed=True)
