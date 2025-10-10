from dataclasses import dataclass
from datetime import datetime
from typing import List

from models import ChatSession


@dataclass(frozen=True)
class ChatDTO:
    id: int
    chat_id: str
    title: str

    @classmethod
    def from_model(cls, chat: ChatSession) -> "ChatDTO":
        """Создает DTO из доменной модели"""
        return cls(
            id=chat.id,
            chat_id=chat.chat_id,
            title=chat.title,
        )


@dataclass(frozen=True)
class UserChatsDTO:
    chats: List[ChatDTO]
    user_id: int
    total_count: int


@dataclass
class DbChatDTO:
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
