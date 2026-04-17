import asyncio
import json
import logging
import re
from typing import Optional

import httpx
from openrouter import OpenRouter
from openrouter.errors import OpenRouterError
from pydantic import ValidationError

from constants.enums import SummaryType
from dto.automoderation import AutoModerationBufferItemDTO, SpamDetectionLLMResultDTO

from .ai_service_base import IAIService, SummaryResult

logger = logging.getLogger(__name__)

SYSTEM_CONTENT = (
    "Ты — эксперт-аналитик коммуникаций. Твоя задача — проанализировать лог чата и выдать глубокую аналитику. "
    "ВАЖНО: Не исользуй HTML-разметку Telegram (<b>, <i>, <code>), а только текст."
    "ПРАВИЛА ОФОРМЛЕНИЯ:\n"
    "- При упоминании пользователей всегда добавляй символ '@' перед их username (например, @username).\n"
    "- Будь лаконичен: фокусируйся на качестве выводов, а не на объеме текста.\n"
    "- В анализе обязательно учитывай список отслеживаемых пользователей: {tracked_users_list}."
    "- Если в списке отслеживаемых пользователей есть пользователь, который не упоминается в логе сообщений, то не упоминай его в анализе."
)
USER_CONTENT_SHORT = (
    "Проведи экспресс-анализ диалога. В начале ответа добавь заголовок: "
    "'📊 Аналитическая выжимка ({msg_count} сообщ.)'\n\n"
    "Сфокусируйся на следующих пунктах:\n"
    "🌡 Атмосфера: [тезисно об общем настроении в чате]\n"
    "🔍 Суть: [топ-1 тема для обсуждения]\n"
    "🤩 Ключевое событие: [ключевое событие, которое все обсуждали]\n"
    "🧐 Участие отсл. пользователей: [общее направление ответов отслеживаемых пользователей: {tracked_users_list}]\n\n"
    "Лог сообщений для анализа:\n{text}"
)

AUTOMOD_SYSTEM = (
    "Ты — эксперт по модерации чатов: выявление спама, ботов и вредоносных аккаунтов. "
    "Проанализируй переданный лог сообщений. Если есть явное подозрение на спамера или бота — "
    "верни один JSON-объект. Если подозрений нет — верни ровно JSON null (без другого текста).\n\n"
    "Формат при срабатывании (один JSON-объект):\n"
    '{"user_tg_id": <int>, "message_id": <int>, "reason": "<краткая причина>", '
    '"username": <строка или null>}\n\n'
    "Поля user_tg_id и message_id должны точно соответствовать одному из сообщений в логе. "
    "Запрещены markdown, обёртки в кодовые блоки и любой текст до или после JSON."
)


def _format_automod_batch(messages: list[AutoModerationBufferItemDTO]) -> str:
    lines: list[str] = []
    for m in messages:
        u = m.username if m.username else "(no username)"
        safe = (m.message_text or "").replace("\n", " ").replace("\r", "")[:400]
        lines.append(
            f"- user_tg_id={m.user_tg_id} message_id={m.message_id} "
            f"username={u!r} text={safe!r}"
        )
    return "\n".join(lines)


def _parse_automod_response(
    raw: str,
    messages: list[AutoModerationBufferItemDTO],
) -> Optional[SpamDetectionLLMResultDTO]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```\s*$", "", text)
        text = text.strip()
    lower = text.lower()
    if lower in ("null", "none", "") or lower == "undefined":
        return None
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        logger.warning(
            "automod LLM: невалидный JSON, chat_snippet=%r",
            text[:500],
        )
        return None
    if data is None:
        return None
    if not isinstance(data, dict):
        logger.warning("automod LLM: ответ не объект JSON")
        return None
    try:
        dto = SpamDetectionLLMResultDTO.model_validate(data)
    except ValidationError as e:
        logger.warning(
            "automod LLM: ошибка Pydantic %s snippet=%r",
            e,
            text[:500],
        )
        return None
    valid = {(m.user_tg_id, m.message_id) for m in messages}
    if (dto.user_tg_id, dto.message_id) not in valid:
        logger.warning(
            "automod LLM: пары id нет в пачке user_tg_id=%s message_id=%s",
            dto.user_tg_id,
            dto.message_id,
        )
        return None
    return dto


USER_CONTENT_FULL = (
    "Проведи глубокий аналитический разбор диалога. В начале ответа добавь заголовок: "
    "'📈 Глубокий анализ обсуждения ({msg_count} сообщ.)'\n\n"
    "Структурируй отчет по следующим категориям:\n"
    "🌡 Атмосфера и тон: [анализ общего настроения в чате]\n"
    "🔍 Суть: [топ-5 тем для обсуждения]\n"
    "🤩 Ключевые события: [топ-3 событий, которые все обсуждали]\n"
    "🤨 Участники: [топ-5 частников и их характеристика]\n"
    "❌ Риски и конфликты: [топ-5 конфликтных ситуаций между участниками и риски для компании]\n"
    "🧐 <b>Участие отсл. пользователей:</b> [общее направление ответов отслеживаемых пользователей: {tracked_users_list}]\n\n"
    "ПРАВИЛА ОФОРМЛЕНИЯ:\n"
    "- Используй буллиты (•) для списков.\n"
    "- Не используй вложенные списки более чем одного уровня.\n"
    "Лог сообщений для анализа:\n{text}"
)


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
            f"Сообщения ({len(messages)} шт.):\n{_format_automod_batch(messages)}"
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
                parsed = _parse_automod_response(str(content), messages)
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
