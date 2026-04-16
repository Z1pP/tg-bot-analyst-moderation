from typing import List, Optional

from dto import AmnestyUserDTO, ChatDTO
from models.chat_session import ChatSession
from repositories import ChatTrackingRepository, UserChatStatusRepository
from services import BotPermissionService, UserService

from .base_get_chats import BaseGetChatsUseCase
from .helpers import safe_telegram_check


class GetChatsWithBannedUserUseCase(BaseGetChatsUseCase):
    """Возвращает чаты где пользователь забанен."""

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
        async def is_banned(chat: ChatSession) -> bool:
            # Среди отслеживаемых чатов администратора ищем где пользователь заблокирован
            status = await self.user_chat_status_repository.get_status(
                user_id=dto.violator_id,
                chat_id=chat.id,
            )
            is_member_banned = await safe_telegram_check(
                self.bot_permission_service.is_member_banned(
                    user_id=int(dto.violator_tgid),
                    chat_tgid=chat.chat_id,
                ),
                False,
                "Не удалось проверить бан в чате %s для %s: %s",
                chat.chat_id,
                dto.violator_tgid,
            )
            return (status and status.is_banned) or is_member_banned

        return await self._get_chats_with_predicate(dto, is_banned)
