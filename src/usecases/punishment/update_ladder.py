from dto.punishment import PunishmentCommandResultDTO, UpdatePunishmentLadderDTO
from models import PunishmentLadder
from repositories import PunishmentLadderRepository
from services import ChatService


class UpdatePunishmentLadderUseCase:
    def __init__(
        self,
        punishment_ladder_repository: PunishmentLadderRepository,
        chat_service: ChatService,
    ):
        self._punishment_ladder_repository = punishment_ladder_repository
        self._chat_service = chat_service

    async def execute(
        self, dto: UpdatePunishmentLadderDTO
    ) -> PunishmentCommandResultDTO:
        chat = await self._chat_service.get_chat_with_archive(chat_id=dto.chat_db_id)
        if not chat:
            return PunishmentCommandResultDTO(
                success=False, error_message="Чат не найден"
            )

        chat_tg_id = chat.chat_id

        # First delete old ladder
        await self._punishment_ladder_repository.delete_ladder_by_chat_id(chat_tg_id)

        # Create new ladder steps
        steps = []
        for item in dto.steps:
            steps.append(
                PunishmentLadder(
                    chat_id=chat_tg_id,
                    step=item.step,
                    punishment_type=item.punishment_type,
                    duration_seconds=item.duration_seconds,
                )
            )

        await self._punishment_ladder_repository.create_ladder(steps)
        return PunishmentCommandResultDTO(success=True)
