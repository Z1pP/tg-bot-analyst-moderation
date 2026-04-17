"""Форматирование пачки для LLM и разбор JSON-ответа автомодерации."""

import json
import logging
import re
from typing import Optional

from pydantic import ValidationError

from dto.automoderation import AutoModerationBufferItemDTO, SpamDetectionLLMResultDTO

logger = logging.getLogger(__name__)


def format_automod_batch(messages: list[AutoModerationBufferItemDTO]) -> str:
    lines: list[str] = []
    for m in messages:
        u = m.username if m.username else "(no username)"
        safe = (m.message_text or "").replace("\n", " ").replace("\r", "")[:400]
        lines.append(
            f"- user_tg_id={m.user_tg_id} message_id={m.message_id} "
            f"username={u!r} text={safe!r}"
        )
    return "\n".join(lines)


def parse_automod_response(
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
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = [data]
    else:
        logger.warning("automod LLM: ответ не массив и не объект JSON")
        return None
    if len(items) == 0:
        return None
    valid = {(m.user_tg_id, m.message_id) for m in messages}
    for item in items:
        if not isinstance(item, dict):
            continue
        try:
            dto = SpamDetectionLLMResultDTO.model_validate(item)
        except ValidationError:
            continue
        if (dto.user_tg_id, dto.message_id) in valid:
            return dto
    logger.warning(
        "automod LLM: нет валидной пары user_tg_id/message_id из пачки, snippet=%r",
        text[:500],
    )
    return None
