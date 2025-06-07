from dataclasses import dataclass
from datetime import datetime

from models import MessageReply


@dataclass
class CreateMessageReplyDTO:
    """DTO для создания новой связи сообщений"""

    chat_id: int
    original_message_url: str
    reply_message_id: int
    reply_user_id: int
    original_message_date: datetime
    reply_message_date: datetime
    response_time_seconds: int


@dataclass
class ResultMessageReplyDTO:
    """DTO для связи сообщений reply"""

    id: int
    original_message_id: int
    reply_message_id: int
    original_user_id: int
    reply_user_id: int
    response_time_seconds: int
    created_at: datetime

    @classmethod
    def from_model(cls, model: "MessageReply") -> "ResultMessageReplyDTO":
        """
        Создает DTO из модели MessageReply

        Args:
            reply: Модель связи сообщений

        Returns:
            MessageReplyDTO: DTO связи сообщений
        """
        return cls(
            id=model.id,
            original_message_id=model.original_message_id,
            reply_message_id=model.reply_message_id,
            original_user_id=model.original_user_id,
            reply_user_id=model.reply_user_id,
            response_time_seconds=model.response_time_seconds,
            created_at=model.created_at,
        )
