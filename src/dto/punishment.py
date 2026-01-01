from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from constants.punishment import PunishmentType


class PunishmentLadderStepDTO(BaseModel):
    step: int
    punishment_type: PunishmentType
    duration_seconds: Optional[int] = None

    model_config = ConfigDict(frozen=True)


class PunishmentLadderResultDTO(BaseModel):
    steps: List[PunishmentLadderStepDTO]
    formatted_text: str

    model_config = ConfigDict(frozen=True)


class UpdatePunishmentLadderDTO(BaseModel):
    chat_db_id: int
    steps: List[PunishmentLadderStepDTO]

    model_config = ConfigDict(frozen=True)


class PunishmentCommandResultDTO(BaseModel):
    success: bool
    error_message: Optional[str] = None

    model_config = ConfigDict(frozen=True)
