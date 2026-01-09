import logging
from datetime import datetime

from config import settings
from constants.enums import AdminActionType, SummaryType
from repositories import ChatRepository, MessageRepository
from services import AdminActionLogService
from services.caching import ICache
from services.chat.summarize import IAIService
from utils.text_preprocessor import format_messages_for_llm

logger = logging.getLogger(__name__)


class GetChatSummaryUseCase:
    def __init__(
        self,
        msg_repository: MessageRepository,
        chat_repository: ChatRepository,
        ai_service: IAIService,
        admin_action_log_service: AdminActionLogService,
        cache: ICache,
    ) -> None:
        self._msg_repo = msg_repository
        self._chat_repo = chat_repository
        self._ai_service = ai_service
        self._admin_action_log_service = admin_action_log_service
        self._cache = cache

    async def execute(
        self,
        chat_id: int,
        summary_type: SummaryType,
        admin_tg_id: str,
        msg_limit: int = 1000,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> str:
        # Пытаемся получить из кеша
        cache_key = f"summary:{chat_id}:{summary_type.value}"
        cached_data = await self._cache.get(cache_key)

        if cached_data:
            summary, last_msg_id = cached_data
            new_msgs_count = await self._msg_repo.count_messages_since(
                chat_id=chat_id, last_id=last_msg_id
            )

            if new_msgs_count < settings.SUMMARY_INVALIDATION_THRESHOLD:
                logger.debug(f"Используем кешированную сводку для чата {chat_id}")
                return summary

        # Если в кеше нет или сообщений много - генерируем заново
        messages = await self._msg_repo.get_messages_for_summary(
            chat_id=chat_id,
            limit=msg_limit,
            start_date=start_date,
            end_date=end_date,
        )

        if not messages:
            return "Нет сообщений для сводки."

        formatted_text, real_count = format_messages_for_llm(messages=messages)

        if not formatted_text:
            return "Нет сообщений для сводки."

        summary = await self._ai_service.summarize_text(
            text=formatted_text, msg_count=real_count, summary_type=summary_type
        )

        # Сохраняем в кеш
        max_id = await self._msg_repo.get_max_message_id(chat_id=chat_id)
        if max_id:
            await self._cache.set(
                key=cache_key,
                value=(summary, max_id),
                ttl=settings.SUMMARY_CACHE_TTL_MINUTES * 60,
            )

        # Логируем действие администратора
        chat = await self._chat_repo.get_chat_by_id(chat_id=chat_id)
        chat_title = chat.title if chat else f"ID: {chat_id}"
        details = f"Чат: {chat_title} ({chat_id}), Тип сводки: {summary_type.value}"
        await self._admin_action_log_service.log_action(
            admin_tg_id=admin_tg_id,
            action_type=AdminActionType.GET_CHAT_SUMMARY_24H,
            details=details,
        )

        return summary
