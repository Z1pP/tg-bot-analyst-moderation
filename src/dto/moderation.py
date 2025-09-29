from dataclasses import dataclass
from typing import Optional

from constants.punishment import PunishmentActions as Actions


@dataclass(frozen=True)
class ModerationActionDTO:
    action: Actions
    # ID и username нарушителя
    user_reply_tgid: str
    user_reply_username: str
    # ID и username администратора
    admin_username: str
    admin_tgid: str
    # ID чата где было сделано замечание
    chat_tgid: str
    chat_title: str
    # ID сообщения с нарушением
    reply_message_id: int
    # Причина наказания
    reason: Optional[str] = None
