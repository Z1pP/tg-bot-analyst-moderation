import logging
from typing import Tuple

from constants.enums import AdminActionType
from models import AdminChatAccess, ChatSession, User
from repositories import ChatRepository, ChatTrackingRepository
from services import AdminActionLogService

logger = logging.getLogger(__name__)


class AddChatToTrackUseCase:
    """
    UseCase для добавления чата в список для отслеживания
    """

    def __init__(
        self,
        chat_repository: ChatRepository,
        chat_tracking_repository: ChatTrackingRepository,
        admin_action_log_service: AdminActionLogService,
    ):
        self._chat_repository = chat_repository
        self._chat_tracking_repository = chat_tracking_repository
        self._admin_action_log_service = admin_action_log_service

    async def execute(
        self,
        chat: ChatSession,
        admin: User,
    ) -> Tuple[AdminChatAccess, bool]:
        """
        Проверяет отслеживается уже чат. Если нет, то заносит в список для
        отслеживания

        Args:
            chat: Объект ChatSession
            admin: Объект User

        Returns:
            Объекты AdminChatAccess, bool
        """
        try:
            # Проверяем чтобы чат уже не отслеживался
            existing_access = await self._chat_tracking_repository.get_access(
                admin_id=admin.id,
                chat_id=chat.id,
            )
            if existing_access:
                return existing_access, True

            # Добавляем чат в список отслеживаемых
            chat_access = await self._chat_tracking_repository.add_chat_to_tracking(
                admin_id=admin.id,
                chat_id=chat.id,
                is_source=False,
                is_target=False,
            )

            # Логируем действие администратора
            details = f"Чат: {chat.title} ({chat.chat_id})"
            await self._admin_action_log_service.log_action(
                admin_tg_id=admin.tg_id,
                action_type=AdminActionType.ADD_CHAT,
                details=details,
            )

            return chat_access, False
        except Exception as e:
            logger.error(
                "Произошла ошибка при добавлении чата в список для отслеживания: %s", e
            )
            raise e
