from typing import Any, Dict, List

from constants.punishment import PunishmentType
from dto.punishment import PunishmentLadderStepDTO, UpdatePunishmentLadderDTO


def map_temp_ladder_to_update_dto(
    chat_db_id: int, temp_ladder: List[Dict[str, Any]]
) -> UpdatePunishmentLadderDTO:
    """
    Преобразует временные данные лестницы из FSM state в UpdatePunishmentLadderDTO.

    Args:
        chat_db_id: ID чата в базе данных
        temp_ladder: Список словарей с данными ступеней из состояния

    Returns:
        UpdatePunishmentLadderDTO: DTO для обновления лестницы
    """
    steps = [
        PunishmentLadderStepDTO(
            step=item["step"],
            punishment_type=PunishmentType[item["punishment_type"]],
            duration_seconds=item["duration_seconds"],
        )
        for item in temp_ladder
    ]
    return UpdatePunishmentLadderDTO(chat_db_id=chat_db_id, steps=steps)
