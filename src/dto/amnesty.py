from dataclasses import dataclass, field
from typing import List, Optional

from constants.punishment import PunishmentType
from .chat_dto import ChatDTO


@dataclass(frozen=True)
class AmnestyUserDTO:
    violator_username: str
    violator_tgid: str
    violator_id: int
    admin_tgid: str
    admin_username: str
    chat_dtos: List[ChatDTO] = field(default_factory=list)


@dataclass(frozen=True, slots=True)
class CancelWarnResultDTO:
    """Результат отмены предупреждения"""

    success: bool
    current_warns_count: int
    next_punishment_type: Optional[PunishmentType]
    next_punishment_duration: Optional[int]
