from typing import List

from dto import ChatDTO
from repositories import ChatTrackingRepository, UserRepository


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

        return [ChatDTO.from_model(chat) for chat in chats]
