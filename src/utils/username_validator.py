import re
from typing import Optional


async def validate_username(username: str) -> Optional[str]:
    if not username or not username.strip():
        return None

    username = username.strip()
    if username.startswith("@"):
        username = username[1:]

    if not re.match(r"^[a-zA-Z0-9_]{5,32}$", username):
        return None

    return username
