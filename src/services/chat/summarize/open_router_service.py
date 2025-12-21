import logging

from openrouter import OpenRouter

from constants.enums import SummaryType

from .ai_service_base import IAIService

logger = logging.getLogger(__name__)

SYSTEM_CONTENT = (
    "Ты помощник, который делает краткие выжимки из логов чата. "
    "Используй подходящие эмодзи для наглядности. "
    "Используй только HTML-разметку, поддерживаемую Telegram: "
    "<b>...</b> для жирного текста, <i>...</i> для курсива, "
    "<code>...</code> для моноширинного текста. "
    "Не используй Markdown, заголовки # или другие HTML-теги."
)
USER_CONTENT_SHORT = (
    "Сделай максимально краткое резюме обсуждения. "
    "В начале ответа обязательно добавь заголовок: "
    "'<b>📊 Краткая сводка за последние {msg_count} сообщений</b>'\n\n{text}"
)
USER_CONTENT_FULL = (
    "Сделай подробное резюме обсуждения, выделив основные темы и решения. "
    "В начале ответа обязательно добавь заголовок: "
    "'<b>📊 Полная сводка за последние {msg_count} сообщений</b>'\n\n{text}"
)


class OpenRouterService(IAIService):
    def __init__(self, api_key: str, model_name: str) -> None:
        super().__init__(model_name)
        self._api_key = api_key

    async def summarize_text(
        self, text: str, msg_count: int, summary_type: SummaryType
    ) -> str:
        async with OpenRouter(api_key=self._api_key) as client:
            try:
                user_content = (
                    USER_CONTENT_SHORT
                    if summary_type == SummaryType.SHORT
                    else USER_CONTENT_FULL
                )
                response = await client.chat.send_async(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": SYSTEM_CONTENT},
                        {
                            "role": "user",
                            "content": user_content.format(
                                text=text, msg_count=msg_count
                            ),
                        },
                    ],
                )

                return response.choices[0].message.content
            except Exception as e:
                logger.error("Unexpected AI error: %s", e, exc_info=True)
                return "❌ Произошла непредвиденная ошибка при генерации сводки."
