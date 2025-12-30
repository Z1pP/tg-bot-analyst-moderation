from dataclasses import dataclass
from typing import List, Optional
from constants.punishment import PunishmentType

@dataclass(frozen=True)
class PunishmentLadderStepDTO:
    step: int
    punishment_type: PunishmentType
    duration_seconds: Optional[int] = None

@dataclass(frozen=True)
class PunishmentLadderResultDTO:
    steps: List[PunishmentLadderStepDTO]
    formatted_text: str

@dataclass(frozen=True)
class UpdatePunishmentLadderDTO:
    chat_db_id: int
    steps: List[PunishmentLadderStepDTO]

@dataclass(frozen=True)
class PunishmentCommandResultDTO:
    success: bool
    error_message: Optional[str] = None

