import logging
from typing import Optional

from constants.enums import AdminActionType
from services import AdminActionLogService, ChatService

logger = logging.getLogger(__name__)


class ToggleAntibotUseCase:
    """
    UseCase для включения/выключения системы антибота в чате.
    """

    def __init__(
        self,
        chat_service: ChatService,
        admin_action_log_service: AdminActionLogService,
    ):
        self.chat_service = chat_service
        self.admin_action_log_service = admin_action_log_service

    async def execute(self, chat_id: int, admin_tg_id: str) -> Optional[bool]:
        """
        Переключает флаг is_antibot_enabled через сервис.

        Args:
            chat_id: Внутренний ID чата
            admin_tg_id: Telegram ID администратора

        Returns:
            Новое состояние флага или None, если чат не найден
        """
        chat = await self.chat_service.get_chat_with_archive(chat_id=chat_id)
        if not chat:
            return None

        new_state = await self.chat_service.toggle_antibot(chat_id)

        if new_state is not None:
            logger.info(
                "UseCase: Статус Антибота для чата ID %s изменен на %s",
                chat_id,
                new_state,
            )

            # Логируем действие администратора
            status_text = "включен" if new_state else "выключен"
            details = f"Чат: {chat.title}, Антибот {status_text}"

            await self.admin_action_log_service.log_action(
                admin_tg_id=admin_tg_id,
                action_type=AdminActionType.ANTIBOT_TOGGLE,
                details=details,
            )

        return new_state
