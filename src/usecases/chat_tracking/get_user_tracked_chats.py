import logging
from typing import List

from models import ChatSession, User
from repositories import ChatTrackingRepository

logger = logging.getLogger(__name__)


class GetUserTrackedChatsUseCase:
    def __init__(self, chat_tracking_repository: ChatTrackingRepository):
        self.chat_tracking_repository = chat_tracking_repository

    async def execute(self, user: User) -> List[ChatSession]:
        """
        Получает список отслеживаемых чатов пользователя.

        Args:
            user: Пользователь

        Returns:
            List[ChatSession]: Список отслеживаемых чатов
        """
        try:
            tracked_chats = await self.chat_tracking_repository.get_all_tracked_chats(
                admin_id=user.id
            )

            logger.debug(
                f"Найдено {len(tracked_chats)} отслеживаемых чатов для user_id={user.id}"
            )

            return tracked_chats

        except Exception as e:
            logger.error(f"Ошибка при получении отслеживаемых чатов: {e}")
            raise
