import logging
from typing import List, Tuple

from models import ChatSession
from repositories import ChatTrackingRepository
from services.user import UserService

logger = logging.getLogger(__name__)


class GetUserTrackedChatsUseCase:
    def __init__(
        self,
        chat_tracking_repository: ChatTrackingRepository,
        user_service: UserService,
    ):
        self.chat_tracking_repository = chat_tracking_repository
        self.user_service = user_service

    async def execute(self, tg_id: str) -> Tuple[List[ChatSession], int]:
        """
        Получает список отслеживаемых чатов пользователя.

        Args:
            tg_id: Telegram ID пользователя

        Returns:
            Tuple[List[ChatSession], int]: (список чатов, user_id)
        """
        try:
            # Получаем пользователя
            user = await self.user_service.get_user(tg_id=tg_id)
            if not user:
                logger.error(f"Пользователь с tg_id={tg_id} не найден")
                return [], 0

            tracked_chats = await self.chat_tracking_repository.get_all_tracked_chats(
                admin_id=user.id
            )

            logger.debug(
                f"Найдено {len(tracked_chats)} отслеживаемых чатов для user_id={user.id}"
            )

            return tracked_chats, user.id

        except Exception as e:
            logger.error(f"Ошибка при получении отслеживаемых чатов: {e}")
            raise
