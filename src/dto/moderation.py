from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from constants.punishment import PunishmentActions as Actions


class ModerationActionDTO(BaseModel):
    action: Actions
    # ID и username нарушителя
    violator_tgid: str
    violator_username: str
    # ID и username администратора
    admin_username: str
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

    model_config = ConfigDict(frozen=True)
