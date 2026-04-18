from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from constants.punishment import PunishmentActions as Actions

from .chat_dto import ChatDTO


class ResultVerifyMember(BaseModel):
    """Результат верификации участника через кнопку антибота."""

    unmuted: bool
    message: str

    model_config = ConfigDict(frozen=True)


class NewMemberRestrictionDTO(BaseModel):
    welcome_text: Optional[str] = None
    is_antibot_enabled: bool = False
    show_welcome_text: bool = False
    auto_delete_welcome_text: bool = False

    model_config = ConfigDict(frozen=True)


class ExecuteModerationInChatsDTO(BaseModel):
    """Входные данные для применения модерации (бан/варн) в нескольких чатах из админ-панели."""

    action: Actions
    chats: tuple[ChatDTO, ...]
    violator_tgid: str
    violator_username: str = ""
    admin_tgid: str
    admin_username: str = ""
    reason: Optional[str] = None

    model_config = ConfigDict(frozen=True)


class ModerationInChatsResultDTO(BaseModel):
    """Результат попыток модерации по чатам (успехи и неудачи по названиям чатов)."""

    success_chats_titles: tuple[str, ...]
    failed_chats_titles: tuple[str, ...]

    model_config = ConfigDict(frozen=True)


class ModerationActionDTO(BaseModel):
    action: Actions
    # ID и username нарушителя
    violator_tgid: str
    violator_username: str = ""
    # ID и username администратора
    admin_username: str = ""
    admin_tgid: str
    # ID чата где было сделано замечание
    chat_tgid: str
    chat_title: str
    # ID сообщения с нарушением
    reply_message_id: Optional[int] = None
    original_message_id: Optional[int] = None
    # Даты создания сообщений
    reply_message_date: Optional[datetime] = None
    original_message_date: Optional[datetime] = None
    # Причина наказания
    reason: Optional[str] = None
    # Флаг вызова из админ-панели (меняет логику отчетов и уведомлений)
    from_admin_panel: bool = False
    # Бан по кнопке «Заблокировать» в карточке авто-модерации (архивный чат)
    from_auto_moderation: bool = False

    model_config = ConfigDict(frozen=True)
