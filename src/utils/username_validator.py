import re
from typing import Optional


async def validate_username(text: str) -> Optional[str]:
    if not text:
        return None

    username = text.lstrip("@")

    if not re.match(r"^[a-zA-Z0-9_]{5,32}$", username):
        return None

    return username
