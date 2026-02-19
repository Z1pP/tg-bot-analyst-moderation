from typing import List, Optional

from dto import AmnestyUserDTO, ChatDTO
from models.chat_session import ChatSession
from repositories import ChatTrackingRepository, PunishmentRepository
from services import UserService

from .base_get_chats import BaseGetChatsUseCase


class GetChatsWithPunishedUserUseCase(BaseGetChatsUseCase):
    """Возвращает чаты где у пользователя есть наказания."""

    def __init__(
        self,
        user_service: UserService,
        chat_tracking_repository: ChatTrackingRepository,
        punishment_repository: PunishmentRepository,
    ):
        super().__init__(user_service, chat_tracking_repository)
        self.punishment_repository = punishment_repository

    async def execute(self, dto: AmnestyUserDTO) -> Optional[List[ChatDTO]]:
        async def has_punishments(chat: ChatSession) -> bool:
            count = await self.punishment_repository.count_punishments(
                user_id=dto.violator_id,
                chat_id=chat.id,
            )
            return count > 0

        return await self._get_chats_with_predicate(dto, has_punishments)
