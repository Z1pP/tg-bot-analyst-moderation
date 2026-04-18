"""Извлечение полей из текста/HTML карточки автомодерации в архивном чате."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from constants import Dialog

_LINK_RE = re.compile(r"t\.me/c/\d+/(\d+)", re.IGNORECASE)


@dataclass(frozen=True)
class AutoModerationCardParsed:
    """Результат разбора карточки (уведомление NotifyAutoModerationHitUseCase)."""

    reason: Optional[str]
    reply_message_id: Optional[int]
    violator_username_hint: Optional[str]


def parse_automoderation_card(
    *,
    text: Optional[str],
    html_text: Optional[str] = None,
) -> AutoModerationCardParsed:
    """
    Парсит причину, id сообщения в рабочем чате (из ссылки t.me/c/...) и подсказку username.

    Args:
        text: Обычный текст сообщения (предпочтителен для строк «Причина:», «Нарушитель:»).
        html_text: HTML-текст (для извлечения ссылки из тега <a href="...">).
    """
    plain = (text or "").strip()
    html = (html_text or plain or "").strip()

    reply_message_id: Optional[int] = None
    match = _LINK_RE.search(html) or _LINK_RE.search(plain)
    if match:
        reply_message_id = int(match.group(1))

    reason: Optional[str] = None
    violator_username_hint: Optional[str] = None
    no_username_label = Dialog.AutoModeration.NO_USERNAME

    for raw_line in plain.split("\n"):
        line = raw_line.strip()
        if line.startswith("Причина:"):
            reason = line.removeprefix("Причина:").strip() or None
        elif line.startswith("Нарушитель:"):
            hint = line.removeprefix("Нарушитель:").strip()
            if hint.startswith("@"):
                hint = hint[1:]
            if hint and hint != no_username_label:
                violator_username_hint = hint

    return AutoModerationCardParsed(
        reason=reason,
        reply_message_id=reply_message_id,
        violator_username_hint=violator_username_hint,
    )
