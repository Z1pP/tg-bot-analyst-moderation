import re
from datetime import datetime, time
from typing import Optional


def parse_and_validate_tg_id(tg_id: str) -> Optional[str]:
    if not tg_id or not tg_id.strip():
        return None

    tg_id = tg_id.strip()
    if tg_id.isdigit():
        return tg_id
    return None


MESSAGE_LINK_PATTERN = r"https://t\.me/(?:c/)?([^/]+)/(?:\d+/)?(\d+)"


def parse_message_link(text: str) -> tuple[str, int] | None:
    import re

    match = re.search(MESSAGE_LINK_PATTERN, text)
    if not match:
        return None

    chat_tgid = match.group(1)
    message_id = int(match.group(2))

    if text.startswith("https://t.me/c/"):
        chat_id = f"-100{chat_tgid}"
    else:
        chat_id = f"@{chat_tgid}"

    return chat_id, message_id


def parse_time(text: str) -> Optional[time]:
    try:
        return datetime.strptime(text, "%H:%M").time()
    except ValueError:
        return None


def parse_tolerance(text: str) -> Optional[int]:
    """
    Парсит отклонение в минутах из строки.

    Args:
        text: Строка с числом (минуты)

    Returns:
        Положительное целое число или None при ошибке
    """
    if not text or not text.strip():
        return None

    try:
        value = int(text.strip())
        if value > 0:
            return value
        return None
    except ValueError:
        return None


def parse_breaks_time(text: str) -> Optional[int]:
    """
    Парсит интервал паузы в минутах из строки.

    Args:
        text: Строка с числом (минуты)

    Returns:
        Неотрицательное целое число или None при ошибке
    """
    if not text or not text.strip():
        return None

    try:
        value = int(text.strip())
        if value >= 0:
            return value
        return None
    except ValueError:
        return None


def parse_duration(text: str) -> Optional[int]:
    """
    Парсит длительность из строки (10m, 2h, 1d) в секунды.

    Args:
        text: Строка с длительностью

    Returns:
        Количество секунд или None при ошибке
    """
    if not text or not text.strip():
        return None

    match = re.match(r"^(\d+)([mhd])$", text.strip().lower())
    if not match:
        return None

    value, unit = int(match.group(1)), match.group(2)
    multipliers = {"m": 60, "h": 3600, "d": 86400}
    return value * multipliers[unit]
