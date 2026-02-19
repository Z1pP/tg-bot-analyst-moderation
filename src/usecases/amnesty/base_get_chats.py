from typing import Awaitable, Callable, List, Optional

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
    ) -> None:
        self.user_service = user_service
        self.chat_tracking_repository = chat_tracking_repository

    async def _get_chats_with_predicate(
        self,
        dto: AmnestyUserDTO,
        chat_predicate: Callable[[ChatSession], Awaitable[bool]],
    ) -> Optional[List[ChatDTO]]:
        """
        Получает отслеживаемые чаты администратора, отфильтрованные по условию.
        """
        admin = await self.user_service.get_user(tg_id=dto.admin_tgid)
        if admin is None:
            return None

        tracked_chats = await self.chat_tracking_repository.get_all_tracked_chats(
            admin_id=admin.id
        )

        filtered_chats = []
        for chat in tracked_chats:
            if await chat_predicate(chat):
                filtered_chats.append(ChatDTO.from_model(chat))

        return filtered_chats if filtered_chats else None

    async def execute(
        self,
        dto: AmnestyUserDTO,
        chat_predicate: Callable[[ChatSession], Awaitable[bool]],
    ) -> Optional[List[ChatDTO]]:
        """Публичный контракт: делегирует в _get_chats_with_predicate."""
        return await self._get_chats_with_predicate(dto, chat_predicate)
