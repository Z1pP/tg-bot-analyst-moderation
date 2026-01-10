import logging
from datetime import time
from typing import Optional

from constants.enums import AdminActionType
from models.chat_session import ChatSession
from services import AdminActionLogService, ChatService

logger = logging.getLogger(__name__)


class UpdateChatWorkHoursUseCase:
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
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        tolerance: Optional[int] = None,
    ) -> Optional[ChatSession]:
        updated_chat = await self._chat_service.update_work_hours(
            chat_id=chat_id,
            start_time=start_time,
            end_time=end_time,
            tolerance=tolerance,
        )

        if updated_chat:
            # Логируем действие администратора
            details_parts = [f"Чат: {updated_chat.title} ({updated_chat.chat_id})"]
            if start_time:
                details_parts.append(
                    f"Новое время начала: {start_time.strftime('%H:%M')}"
                )
            if end_time:
                details_parts.append(
                    f"Новое время окончания: {end_time.strftime('%H:%M')}"
                )
            if tolerance is not None:
                details_parts.append(f"Новое отклонение: {tolerance} мин.")

            await self._admin_action_log_service.log_action(
                admin_tg_id=admin_tg_id,
                action_type=AdminActionType.REPORT_TIME_SETTING,
                details=", ".join(details_parts),
            )

        return updated_chat
