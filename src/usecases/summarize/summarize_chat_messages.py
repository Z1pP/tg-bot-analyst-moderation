from datetime import datetime

from constants.enums import SummaryType
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

    async def execute(
        self,
        chat_id: int,
        summary_type: SummaryType,
        msg_limit: int = 1000,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> str:
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

        return summary
