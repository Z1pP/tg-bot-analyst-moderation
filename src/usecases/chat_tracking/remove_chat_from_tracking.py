import logging
from typing import Optional

from repositories import ChatRepository, ChatTrackingRepository, UserRepository

logger = logging.getLogger(__name__)


class RemoveChatFromTrackingUseCase:
    def __init__(
        self,
        chat_tracking_repository: ChatTrackingRepository,
        user_repository: UserRepository,
        chat_repository: ChatRepository,
    ):
        self.chat_tracking_repository = chat_tracking_repository
        self.chat_repository = chat_repository
        self.user_repository = user_repository

    async def execute(self, user_id: int, chat_id: int) -> tuple[bool, Optional[str]]:
        """
        Удаляет чат из отслеживания.

        Args:
            user_id: ID пользователя
            chat_id: ID чата

        Returns:
            tuple[bool, Optional[str]]: (успех, сообщение об ошибке)
        """
        try:
            # Получаем пользователя и чат
            admin = await self.user_repository.get_user_by_id(user_id)
            chat = await self.chat_repository.get_chat_by_id(chat_id)

            if not admin:
                logger.error(f"Пользователь {user_id} не найден")
                return False, "Пользователь не найден"

            if not chat:
                logger.error(f"Чат {chat_id} не найден")
                return False, "Чат не найден"

            success = await self.chat_tracking_repository.remove_chat_from_tracking(
                admin_id=admin.id,
                chat_id=chat.id,
            )

            if success:
                logger.info(
                    f"Чат '{chat.title}' успешно удален из отслеживания админом {admin.username}"
                )
                return True, None
            else:
                logger.warning(f"Чат '{chat.title}' не найден в отслеживании")
                return False, "Чат не найден в отслеживании"

        except Exception as e:
            logger.error(f"Ошибка при удалении чата из отслеживания: {e}")
            raise
