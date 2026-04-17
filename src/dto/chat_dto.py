from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from models import ChatSession


class GetChatWithArchiveDTO(BaseModel):
    """DTO для получения чата с архивным каналом по id или tgid."""

    chat_id: Optional[int] = None
    chat_tgid: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class GenerateArchiveBindHashDTO(BaseModel):
    """DTO для генерации hash привязки архивного чата."""

    chat_id: int
    admin_tg_id: int

    model_config = ConfigDict(frozen=True)


class BindArchiveChatDTO(BaseModel):
    """DTO для привязки архивного чата к рабочему по hash."""

    bind_hash: str
    archive_chat_tgid: str
    archive_chat_title: str

    model_config = ConfigDict(frozen=True)


class ChatDTO(BaseModel):
    id: int
    tg_id: str
    title: str
    is_antibot_enabled: bool
    is_auto_moderation_enabled: bool
    welcome_text: Optional[str] = None

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_model(cls, chat: ChatSession) -> "ChatDTO":
        """Создает DTO из доменной модели"""
        is_antibot_enabled = False
        is_auto_moderation_enabled = False
        welcome_text = None

        if chat.settings:
            is_antibot_enabled = chat.settings.is_antibot_enabled
            is_auto_moderation_enabled = chat.settings.is_auto_moderation_enabled
            welcome_text = chat.settings.welcome_text

        return cls(
            id=chat.id,
            tg_id=chat.chat_id,
            title=chat.title or "",
            is_antibot_enabled=is_antibot_enabled,
            is_auto_moderation_enabled=is_auto_moderation_enabled,
            welcome_text=welcome_text,
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

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_model(cls, chat: ChatSession) -> "DbChatDTO":
        """Создает DTO из доменной модели"""
        return cls(
            id=chat.id,
            chat_id=chat.chat_id,
            title=chat.title or "",
            created_at=chat.created_at,
        )
