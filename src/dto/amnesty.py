from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from constants.punishment import PunishmentType

from .chat_dto import ChatDTO


class AmnestyUserDTO(BaseModel):
    violator_username: str
    violator_tgid: str
    violator_id: int
    admin_tgid: str
    admin_username: str
    chat_dtos: List[ChatDTO] = Field(default_factory=list)

    model_config = ConfigDict(frozen=True)


class CancelWarnResultDTO(BaseModel):
    """Результат отмены предупреждения"""

    success: bool
    current_warns_count: int
    next_punishment_type: Optional[PunishmentType]
    next_punishment_duration: Optional[int]

    model_config = ConfigDict(frozen=True)
