from repositories import ChatTrackingRepository
from services.user import UserService


class GetAllChatsUseCase:
    def __init__(
        self,
        chat_tracking_repository: ChatTrackingRepository,
        user_service: UserService,
    ):
        self._chat_tracking_repository = chat_tracking_repository
        self._user_service = user_service

    async def execute(self, username: str):
        user = await self._user_service.get_user(username)

        if not user:
            return []

        chats = await self._chat_tracking_repository.get_all_admin_chats(user.id)

        return chats
