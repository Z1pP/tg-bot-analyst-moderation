import asyncio
import logging
from typing import Optional

import httpx
from openrouter import OpenRouter
from openrouter.errors import OpenRouterError

from constants.enums import SummaryType
from constants.promps import (
    AUTOMOD_SYSTEM,
    SYSTEM_CONTENT,
    USER_CONTENT_FULL,
    USER_CONTENT_SHORT,
)
from dto.automoderation import AutoModerationBufferItemDTO, SpamDetectionLLMResultDTO
from utils.automoderation_llm import format_automod_batch, parse_automod_response

from .ai_service_base import IAIService, SummaryResult

logger = logging.getLogger(__name__)


class OpenRouterService(IAIService):
    def __init__(self, api_key: str, model_name: str) -> None:
        super().__init__(model_name)
        self._api_key = api_key

    async def summarize_text(
        self,
        text: str,
        msg_count: int,
        summary_type: SummaryType,
        tracked_users: list[str],
    ) -> SummaryResult:
        async with OpenRouter(api_key=self._api_key) as client:
            try:
                user_content = (
                    USER_CONTENT_SHORT
                    if summary_type == SummaryType.SHORT
                    else USER_CONTENT_FULL
                )
                tracked_users_str = (
                    ", ".join(tracked_users) if tracked_users else "отсутствуют"
                )
                response = await client.chat.send_async(
                    model=self._model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": SYSTEM_CONTENT.format(
                                tracked_users_list=tracked_users_str
                            ),
                        },
                        {
                            "role": "user",
                            "content": user_content.format(
                                text=text,
                                msg_count=msg_count,
                                tracked_users_list=tracked_users_str,
                            ),
                        },
                    ],
                )

                if not response.choices:
                    logger.error("OpenRouter response has no choices.")
                    return SummaryResult(
                        status_code=502,
                        summary="❌ Произошла непредвиденная ошибка при генерации сводки.",
                    )

                first_choice = response.choices[0]
                message = getattr(first_choice, "message", None)
                content = getattr(message, "content", None)

                if not content:
                    logger.error("OpenRouter response has no content.")
                    return SummaryResult(
                        status_code=502,
                        summary="❌ Произошла непредвиденная ошибка при генерации сводки.",
                    )

                return SummaryResult(status_code=200, summary=content)
            except OpenRouterError as exc:
                logger.error(
                    "OpenRouter API error: %s (status=%s)",
                    exc,
                    exc.status_code,
                    exc_info=True,
                )
                return SummaryResult(
                    status_code=exc.status_code,
                    summary="❌ Произошла непредвиденная ошибка при генерации сводки.",
                )
            except httpx.HTTPError as exc:
                logger.error("OpenRouter network error: %s", exc, exc_info=True)
                return SummaryResult(
                    status_code=503,
                    summary="❌ Произошла непредвиденная ошибка при генерации сводки.",
                )

    async def analyze_spam_batch(
        self,
        chat_title: str,
        messages: list[AutoModerationBufferItemDTO],
    ) -> Optional[SpamDetectionLLMResultDTO]:
        if not messages:
            return None
        user_content = (
            f"Название чата: {chat_title}\n\n"
            f"Сообщения ({len(messages)} шт.):\n{format_automod_batch(messages)}"
        )
        async with OpenRouter(api_key=self._api_key) as client:
            try:
                response = await client.chat.send_async(
                    model=self._model_name,
                    messages=[
                        {"role": "system", "content": AUTOMOD_SYSTEM},
                        {"role": "user", "content": user_content},
                    ],
                )
                if not response.choices:
                    logger.error(
                        "automod OpenRouter: нет choices, chat_title=%s",
                        chat_title,
                    )
                    return None
                first_choice = response.choices[0]
                message = getattr(first_choice, "message", None)
                content = getattr(message, "content", None)
                if not content or not str(content).strip():
                    logger.warning(
                        "automod OpenRouter: пустой content, chat_title=%s",
                        chat_title,
                    )
                    return None
                parsed = parse_automod_response(str(content), messages)
                if parsed:
                    logger.info(
                        "automod: срабатывание LLM chat_title=%s user_tg_id=%s",
                        chat_title,
                        parsed.user_tg_id,
                    )
                return parsed
            except OpenRouterError as exc:
                logger.error(
                    "automod OpenRouter API error chat_title=%s: %s (status=%s)",
                    chat_title,
                    exc,
                    getattr(exc, "status_code", None),
                    exc_info=True,
                )
                return None
            except httpx.HTTPError as exc:
                logger.error(
                    "automod OpenRouter HTTP error chat_title=%s: %s",
                    chat_title,
                    exc,
                    exc_info=True,
                )
                return None
            except (asyncio.TimeoutError, OSError) as exc:
                logger.error(
                    "automod OpenRouter timeout/OS chat_title=%s: %s",
                    chat_title,
                    exc,
                    exc_info=True,
                )
                return None
            except (TypeError, ValueError, AttributeError) as exc:
                logger.error(
                    "automod OpenRouter внутренняя ошибка chat_title=%s: %s",
                    chat_title,
                    exc,
                    exc_info=True,
                )
                return None
