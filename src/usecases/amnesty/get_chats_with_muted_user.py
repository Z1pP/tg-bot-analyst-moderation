from typing import List, Optional

from dto import AmnestyUserDTO, ChatDTO
from models.chat_session import ChatSession
from repositories import ChatTrackingRepository, UserChatStatusRepository
from services import UserService, BotPermissionService

from .base_get_chats import BaseGetChatsUseCase
from .helpers import safe_telegram_check


class GetChatsWithMutedUserUseCase(BaseGetChatsUseCase):
    """Возвращает чаты где пользователь замучен."""

    def __init__(
        self,
        user_service: UserService,
        chat_tracking_repository: ChatTrackingRepository,
        user_chat_status_repository: UserChatStatusRepository,
        bot_permission_service: BotPermissionService,
    ) -> None:
        super().__init__(user_service, chat_tracking_repository)
        self.user_chat_status_repository = user_chat_status_repository
        self.bot_permission_service = bot_permission_service

    async def execute(self, dto: AmnestyUserDTO) -> Optional[List[ChatDTO]]:
        async def is_muted(chat: ChatSession) -> bool:
            # Среди отслеживаемых чатов администратора ищем где пользователь замучен
            status = await self.user_chat_status_repository.get_status(
                user_id=dto.violator_id,
                chat_id=chat.id,
            )
            is_member_muted = await safe_telegram_check(
                self.bot_permission_service.is_member_muted(
                    tg_id=dto.violator_tgid,
                    chat_tg_id=chat.chat_id,
                ),
                False,
                "Не удалось проверить mute в чате %s для %s: %s",
                chat.chat_id,
                dto.violator_tgid,
            )
            return (status and status.is_muted) or is_member_muted

        return await self._get_chats_with_predicate(dto, is_muted)
