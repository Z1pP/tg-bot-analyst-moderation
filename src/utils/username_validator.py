from typing import Optional


def parse_and_validate_username(text: str) -> Optional[str]:
    if not text or not text.strip():
        return None

    text = text.strip()
    if text.startswith("@"):
        text = text[1:]
        return text
    return None


def parse_and_validate_tg_id(tg_id: str) -> Optional[str]:
    if not tg_id or not tg_id.strip():
        return None

    tg_id = tg_id.strip()
    if tg_id.isdigit():
        return tg_id
    return None
