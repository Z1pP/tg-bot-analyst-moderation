import logging
from typing import Optional

from constants.enums import AdminActionType
from models.chat_session import ChatSession
from services import AdminActionLogService, ChatService

logger = logging.getLogger(__name__)


class UpdateChatWelcomeTextUseCase:
    def __init__(
        self,
        chat_service: ChatService,
        admin_action_log_service: AdminActionLogService,
    ):
        self._chat_service = chat_service
        self._admin_action_log_service = admin_action_log_service

    async def execute(
        self,
        chat_id: int,
        admin_tg_id: str,
        welcome_text: str,
    ) -> Optional[ChatSession]:
        """
        Обновляет приветственный текст чата и логирует действие.
        """
        updated_chat = await self._chat_service.update_welcome_text(
            chat_id=chat_id,
            welcome_text=welcome_text,
        )

        if updated_chat:
            # Логируем действие администратора
            details = f"Чат: {updated_chat.title} ({updated_chat.chat_id}), приветствие изменено"

            await self._admin_action_log_service.log_action(
                admin_tg_id=admin_tg_id,
                action_type=AdminActionType.REPORT_TIME_SETTING,  # Можно использовать существующий или добавить новый тип
                details=details,
            )

        return updated_chat
