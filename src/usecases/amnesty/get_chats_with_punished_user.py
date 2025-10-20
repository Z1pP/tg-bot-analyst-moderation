from typing import List, Optional
from dto import ChatDTO, AmnestyUserDTO
from repositories import ChatTrackingRepository
from services import UserService, PunishmentService


class GetChatsWithPunishedUserUseCase:
    def __init__(
        self,
        user_service: UserService,
        chat_tracking_repository: ChatTrackingRepository,
        punishment_service: PunishmentService,
    ):
        self.user_service = user_service
        self.chat_tracking_repository = chat_tracking_repository
        self.punishment_service = punishment_service

    async def execute(self, dto: AmnestyUserDTO) -> Optional[List[ChatDTO]]:
        admin = await self.user_service.get_user(tg_id=dto.admin_tgid)

        tracked_chats = await self.chat_tracking_repository.get_all_tracked_chats(
            admin_id=admin.id
        )

        chats_with_punishments = (
            await self.punishment_service.get_chats_with_punishments(
                user_id=dto.violator_id,
                tracked_chats=tracked_chats,
            )
        )

        if not chats_with_punishments:
            return None

        chat_dtos = [
            ChatDTO(
                id=chat.id,
                tg_id=chat.chat_id,
                title=chat.title,
            )
            for chat in chats_with_punishments
        ]

        return chat_dtos
