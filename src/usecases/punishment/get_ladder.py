from typing import List

from dto.punishment import PunishmentLadderResultDTO, PunishmentLadderStepDTO
from models import PunishmentLadder
from repositories import PunishmentLadderRepository
from services import ChatService, PunishmentService


class GetPunishmentLadderUseCase:
    def __init__(
        self,
        punishment_ladder_repository: PunishmentLadderRepository,
        chat_service: ChatService,
        punishment_service: PunishmentService,
    ):
        self._punishment_ladder_repository = punishment_ladder_repository
        self._chat_service = chat_service
        self._punishment_service = punishment_service

    async def execute(self, chat_db_id: int) -> PunishmentLadderResultDTO:
        chat = await self._chat_service.get_chat_with_archive(chat_id=chat_db_id)
        if not chat:
            return PunishmentLadderResultDTO(steps=[], formatted_text="")

        chat_tg_id = chat.chat_id
        ladder = await self._punishment_ladder_repository.get_ladder_by_chat_id(
            chat_id=chat_tg_id
        )

        steps = [
            PunishmentLadderStepDTO(
                step=p.step,
                punishment_type=p.punishment_type,
                duration_seconds=p.duration_seconds,
            )
            for p in ladder
        ]

        formatted_text = self._punishment_service.format_ladder_text(ladder)

        return PunishmentLadderResultDTO(steps=steps, formatted_text=formatted_text)
