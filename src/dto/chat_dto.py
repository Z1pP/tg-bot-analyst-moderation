from datetime import datetime, time
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from models import ChatSession
from models.chat_settings import ChatSettings


class ChatSessionCacheDTO(BaseModel):
    """
    Снимок чата и chat_settings для Redis (без pickle ORM — без DetachedInstanceError).
    """

    id: int
    chat_id: str
    title: Optional[str]
    archive_chat_id: Optional[str]
    settings_id: Optional[int] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    tolerance: Optional[int] = None
    breaks_time: Optional[int] = None
    is_antibot_enabled: bool = False
    is_auto_moderation_enabled: bool = False
    welcome_text: Optional[str] = None
    auto_delete_welcome_text: bool = False
    show_welcome_text: bool = False

    model_config = ConfigDict(frozen=True)

    @classmethod
    def from_chat_session(cls, chat: ChatSession) -> "ChatSessionCacheDTO":
        """Собирает DTO из отсоединённого ChatSession с загруженными settings (как после репозитория)."""
        raw = getattr(chat, "settings", None)
        s = raw if isinstance(raw, ChatSettings) else None
        return cls(
            id=chat.id,
            chat_id=chat.chat_id,
            title=chat.title,
            archive_chat_id=chat.archive_chat_id,
            settings_id=s.id if s else None,
            start_time=s.start_time if s else None,
            end_time=s.end_time if s else None,
            tolerance=s.tolerance if s else None,
            breaks_time=s.breaks_time if s else None,
            is_antibot_enabled=s.is_antibot_enabled if s else False,
            is_auto_moderation_enabled=s.is_auto_moderation_enabled if s else False,
            welcome_text=s.welcome_text if s else None,
            auto_delete_welcome_text=s.auto_delete_welcome_text if s else False,
            show_welcome_text=s.show_welcome_text if s else False,
        )


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
