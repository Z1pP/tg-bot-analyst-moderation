import logging

from models import AdminChatAccess, ChatSession, User
from repositories import ChatRepository, ChatTrackingRepository

logger = logging.getLogger(__name__)


class AddChatToTrackUseCase:
    """
    UseCase для добавления чата в список для отслеживания
    """

    def __init__(
        self,
        chat_repository: ChatRepository,
        chat_tracking_repository: ChatTrackingRepository,
    ):
        self._chat_repository = chat_repository
        self._chat_tracking_repository = chat_tracking_repository

    async def execute(
        self,
        chat: ChatSession,
        admin: User,
    ) -> AdminChatAccess:
        """
        Добавляет чат в отслеживание.

        Args:
            chat: Объект ChatSession
            admin: Объект User

        Returns:
            Объект AdminChatAccess
        """
        try:
            # Создаем связь между чатом и админом
            await self._chat_tracking_repository.add_chat_to_tracking(
                admin_id=admin.id,
                chat_id=chat.id,
                is_source=False,
                is_target=False,
            )
        except Exception as e:
            logger.error(
                "Произошла ошибка при добавлении чата в список для отслеживания: %s", e
            )
            raise e
