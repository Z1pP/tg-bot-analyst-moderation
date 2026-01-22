import logging
from typing import Optional

from services import ChatService

logger = logging.getLogger(__name__)


class ToggleWelcomeTextUseCase:
    """UseCase для включения/выключения приветственного текста в чате."""

    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    async def execute(self, chat_id: int) -> Optional[bool]:
        """
        Переключает флаг show_welcome_text через сервис.

        Args:
            chat_id: Внутренний ID чата

        Returns:
            Новое состояние флага или None, если чат не найден
        """
        new_state = await self.chat_service.toggle_show_welcome_text(chat_id)

        if new_state is None:
            logger.warning(
                "UseCase: Чат не найден при переключении приветствия: %s",
                chat_id,
            )

        return new_state
