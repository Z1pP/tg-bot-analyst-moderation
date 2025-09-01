import logging

from models import ChatSession, User
from repositories import ChatTrackingRepository

logger = logging.getLogger(__name__)


class RemoveChatFromTrackingUseCase:
    def __init__(self, chat_tracking_repository: ChatTrackingRepository):
        self.chat_tracking_repository = chat_tracking_repository

    async def execute(self, admin: User, chat: ChatSession) -> bool:
        """
        Удаляет чат из отслеживания.

        Args:
            admin: Администратор
            chat: Чат для удаления

        Returns:
            bool: True если чат был удален, False если не найден
        """
        try:
            success = await self.chat_tracking_repository.remove_chat_from_tracking(
                admin_id=admin.id,
                chat_id=chat.id,
            )

            if success:
                logger.info(
                    f"Чат '{chat.title}' успешно удален из отслеживания админом {admin.username}"
                )
            else:
                logger.warning(f"Чат '{chat.title}' не найден в отслеживании")

            return success

        except Exception as e:
            logger.error(f"Ошибка при удалении чата из отслеживания: {e}")
            raise
