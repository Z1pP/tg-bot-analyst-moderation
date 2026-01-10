import logging
from typing import Optional

from services import ChatService

logger = logging.getLogger(__name__)


class ToggleAntibotUseCase:
    """
    UseCase для включения/выключения системы антибота в чате.
    """

    def __init__(self, chat_service: ChatService):
        self.chat_service = chat_service

    async def execute(self, chat_id: int) -> Optional[bool]:
        """
        Переключает флаг is_antibot_enabled через сервис.

        Args:
            chat_id: Внутренний ID чата

        Returns:
            Новое состояние флага или None, если чат не найден
        """
        new_state = await self.chat_service.toggle_antibot(chat_id)

        if new_state is not None:
            logger.info(
                "UseCase: Статус Антибота для чата ID %s изменен на %s",
                chat_id,
                new_state,
            )

        return new_state
