from typing import List

from dto import ChatDTO
from repositories import ChatTrackingRepository, UserChatStatusRepository
from services import UserService


class GetChatsWithBannedUserUseCase:
    def __init__(
        self,
        user_service: UserService,
        chat_tracking_repository: ChatTrackingRepository,
        user_chat_status_repository: UserChatStatusRepository,
    ):
        self.user_service = user_service
        self.chat_tracking_repository = chat_tracking_repository
        self.user_chat_status_repository = user_chat_status_repository

    async def execute(self, admin_tgid: str, violator_tgid: str) -> List[ChatDTO]:
        admin = await self.user_service.get_user(tg_id=admin_tgid)
        violator = await self.user_service.get_user(tg_id=violator_tgid)

        if not admin or not violator:
            return []

        tracked_chats = await self.chat_tracking_repository.get_all_tracked_chats(
            admin_id=admin.id
        )

        result = []
        for chat in tracked_chats:
            status = await self.user_chat_status_repository.get_status(
                user_id=violator.id,
                chat_id=chat.id,
            )

            if status and status.is_banned:
                result.append(
                    ChatDTO(
                        id=chat.id,
                        chat_id=chat.chat_id,
                        title=chat.title,
                    )
                )

        return result
