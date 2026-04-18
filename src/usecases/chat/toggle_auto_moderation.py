"""Переключение флага автомодерации по чату."""

import logging
from typing import Optional

from constants.enums import AdminActionType
from services import AdminActionLogService, ChatService

logger = logging.getLogger(__name__)


class ToggleAutoModerationUseCase:
    """UseCase для включения/выключения LLM-автомодерации."""

    def __init__(
        self,
        chat_service: ChatService,
        admin_action_log_service: AdminActionLogService,
    ) -> None:
        self.chat_service = chat_service
        self.admin_action_log_service = admin_action_log_service

    async def execute(self, chat_id: int, admin_tg_id: str) -> Optional[bool]:
        chat = await self.chat_service.get_chat_with_archive(chat_id=chat_id)
        if not chat:
            return None

        new_state = await self.chat_service.toggle_auto_moderation(chat_id)
        if new_state is not None:
            logger.info(
                "Автомодерация для чата id=%s переключена в %s",
                chat_id,
                new_state,
            )
            status_text = "включена" if new_state else "выключена"
            details = f"Чат: {chat.title}, Автомодерация {status_text}"
            await self.admin_action_log_service.log_action(
                admin_tg_id=admin_tg_id,
                action_type=AdminActionType.AUTO_MODERATION_TOGGLE,
                details=details,
            )
        return new_state
