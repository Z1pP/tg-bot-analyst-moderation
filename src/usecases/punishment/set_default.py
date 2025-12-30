from dto.punishment import PunishmentCommandResultDTO
from repositories import PunishmentLadderRepository
from services import ChatService


class SetDefaultPunishmentLadderUseCase:
    def __init__(
        self,
        punishment_ladder_repository: PunishmentLadderRepository,
        chat_service: ChatService,
    ):
        self._punishment_ladder_repository = punishment_ladder_repository
        self._chat_service = chat_service

    async def execute(self, chat_db_id: int) -> PunishmentCommandResultDTO:
        chat = await self._chat_service.get_chat_with_archive(chat_id=chat_db_id)
        if not chat:
            return PunishmentCommandResultDTO(
                success=False, error_message="Чат не найден"
            )

        chat_tg_id = chat.chat_id
        await self._punishment_ladder_repository.delete_ladder_by_chat_id(
            chat_id=chat_tg_id
        )
        return PunishmentCommandResultDTO(success=True)
