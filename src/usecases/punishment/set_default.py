from constants.enums import AdminActionType
from dto.punishment import PunishmentCommandResultDTO
from repositories import PunishmentLadderRepository
from services import AdminActionLogService, ChatService


class SetDefaultPunishmentLadderUseCase:
    def __init__(
        self,
        punishment_ladder_repository: PunishmentLadderRepository,
        chat_service: ChatService,
        admin_action_log_service: AdminActionLogService,
    ):
        self._punishment_ladder_repository = punishment_ladder_repository
        self._chat_service = chat_service
        self._admin_action_log_service = admin_action_log_service

    async def execute(
        self, chat_db_id: int, admin_tg_id: str
    ) -> PunishmentCommandResultDTO:
        chat = await self._chat_service.get_chat_with_archive(chat_id=chat_db_id)
        if not chat:
            return PunishmentCommandResultDTO(
                success=False, error_message="Чат не найден"
            )

        chat_tg_id = chat.chat_id
        await self._punishment_ladder_repository.delete_ladder_by_chat_id(
            chat_id=chat_tg_id
        )

        # Логируем действие администратора
        chat_title = chat.title if chat else f"ID: {chat_db_id}"
        details = f"Чат: {chat_title} ({chat_db_id}), Действие: сброс до настроек по умолчанию"
        await self._admin_action_log_service.log_action(
            admin_tg_id=admin_tg_id,
            action_type=AdminActionType.PUNISHMENT_SETTING,
            details=details,
        )

        return PunishmentCommandResultDTO(success=True)
