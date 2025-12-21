from repositories import MessageRepository
from services.caching import ICache
from services.chat.summarize import IAIService
from utils.text_preprocessor import format_messages_for_llm


class GetChatSummaryUseCase:
    def __init__(
        self,
        msg_repository: MessageRepository,
        ai_service: IAIService,
        cache_service: ICache,
    ) -> None:
        self._msg_repo = msg_repository
        self._ai_service = ai_service
        self._cache = cache_service

    async def execute(self, user_id: int, chat_id: int, msg_limit: int = 1000) -> str:
        # Проверка блокировки в Redis (1 запрос в сутки на пару пользователь-чат)
        lock_key = f"ai_summary_lock:{chat_id}:{user_id}"
        if await self._cache.get(lock_key):
            return "⚠️ Вы уже запрашивали сводку для этого чата за последние 24 часа."

        messages = await self._msg_repo.get_messages_for_summary(
            chat_id=chat_id,
            limit=msg_limit,
        )

        if not messages:
            return "Нет сообщений для сводки."

        formatted_text = format_messages_for_llm(messages=messages)

        summary = await self._ai_service.summarize_text(text=formatted_text)

        # Устанавливаем блокировку на 24 часа после успешного (или любого?) запроса
        # В данном случае, даже если ИИ вернул ошибку, лучше залочить, чтобы не спамили ошибками
        await self._cache.set(lock_key, "1", ttl=86400)

        return summary
