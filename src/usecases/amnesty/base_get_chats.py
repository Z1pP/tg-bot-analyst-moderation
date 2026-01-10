from typing import Callable, List, Optional

from dto import AmnestyUserDTO, ChatDTO
from models.chat_session import ChatSession
from repositories import ChatTrackingRepository
from services import UserService


class BaseGetChatsUseCase:
    """Базовый UseCase для получения чатов по условию."""

    def __init__(
        self,
        user_service: UserService,
        chat_tracking_repository: ChatTrackingRepository,
    ):
        self.user_service = user_service
        self.chat_tracking_repository = chat_tracking_repository

    async def execute(
        self,
        dto: AmnestyUserDTO,
        filter_func: Callable[[ChatSession], bool],
    ) -> Optional[List[ChatDTO]]:
        """
        Получает отслеживаемые чаты администратора, отфильтрованные по условию.

        Args:
            dto: DTO с данными пользователя и администратора
            filter_func: Async функция фильтрации чатов

        Returns:
            Список ChatDTO или None если чаты не найдены
        """
        admin = await self.user_service.get_user(tg_id=dto.admin_tgid)

        tracked_chats = await self.chat_tracking_repository.get_all_tracked_chats(
            admin_id=admin.id
        )

        filtered_chats = []
        for chat in tracked_chats:
            if await filter_func(chat):
                filtered_chats.append(ChatDTO.from_model(chat))

        return filtered_chats if filtered_chats else None
