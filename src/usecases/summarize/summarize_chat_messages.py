from repositories import MessageRepository
from services.chat.summarize import IAIService
from utils.text_preprocessor import format_messages_for_llm


class GetChatSummaryUseCase:
    def __init__(
        self,
        msg_repository: MessageRepository,
        ai_service: IAIService,
    ) -> None:
        self._msg_repo = msg_repository
        self._ai_service = ai_service

    async def execute(self, user_id: int, chat_id: int, msg_limit: int = 1000) -> str:
        messages = await self._msg_repo.get_messages_for_summary(
            chat_id=chat_id,
            limit=msg_limit,
        )

        if not messages:
            return "Нет сообщений для сводки."

        formatted_text = format_messages_for_llm(messages=messages)

        summary = await self._ai_service.summarize_text(text=formatted_text)

        return summary
