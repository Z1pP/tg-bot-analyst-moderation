from typing import List
from repositories import ChatTrackingRepository, UserRepository
from dto import ChatDTO


class GetTrackedChatsUseCase:
    def __init__(
        self,
        chat_tracking_repository: ChatTrackingRepository,
        user_repository: UserRepository,
    ):
        self._chat_tracking_repository = chat_tracking_repository
        self._user_repository = user_repository

    async def execute(self, tg_id: str) -> List[ChatDTO]:
        user = await self._user_repository.get_user_by_tg_id(tg_id=tg_id)

        if not user:
            return []

        chats = await self._chat_tracking_repository.get_all_tracked_chats(
            admin_id=user.id
        )

        return [
            ChatDTO(id=chat.id, tg_id=chat.chat_id, title=chat.title) for chat in chats
        ]
