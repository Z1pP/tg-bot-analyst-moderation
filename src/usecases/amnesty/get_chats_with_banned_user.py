from typing import List, Optional

from dto import AmnestyUserDTO, ChatDTO
from repositories import ChatTrackingRepository, UserChatStatusRepository
from services import UserService

from .base_get_chats import BaseGetChatsUseCase


class GetChatsWithBannedUserUseCase(BaseGetChatsUseCase):
    """Возвращает чаты где пользователь забанен."""

    def __init__(
        self,
        user_service: UserService,
        chat_tracking_repository: ChatTrackingRepository,
        user_chat_status_repository: UserChatStatusRepository,
    ):
        super().__init__(user_service, chat_tracking_repository)
        self.user_chat_status_repository = user_chat_status_repository

    async def execute(self, dto: AmnestyUserDTO) -> Optional[List[ChatDTO]]:
        async def is_banned(chat):
            # Среди отслеживаемых чатов администратора ищем где пользователь заблокирован
            status = await self.user_chat_status_repository.get_status(
                user_id=dto.violator_id,
                chat_id=chat.id,
            )
            return status and status.is_banned

        return await super().execute(dto, is_banned)
