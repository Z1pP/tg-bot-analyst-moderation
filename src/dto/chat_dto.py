from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict

from models import ChatSession


class ChatDTO(BaseModel):
    id: int
    tg_id: str
    title: str

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_model(cls, chat: ChatSession) -> "ChatDTO":
        """Создает DTO из доменной модели"""
        return cls(
            id=chat.id,
            tg_id=chat.chat_id,
            title=chat.title,
        )


class UserChatsDTO(BaseModel):
    chats: List[ChatDTO]
    user_id: int
    total_count: int

    model_config = ConfigDict(frozen=True)


class DbChatDTO(BaseModel):
    """DTO для чата из базы данных"""

    id: int
    chat_id: str
    title: str
    created_at: datetime

    @classmethod
    def from_model(cls, chat: ChatSession) -> "DbChatDTO":
        """Создает DTO из доменной модели"""
        return cls(
            id=chat.id,
            chat_id=chat.chat_id,
            title=chat.title,
            created_at=chat.created_at,
        )
