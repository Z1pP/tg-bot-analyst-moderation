import re
from typing import Optional

from aiogram.enums import ParseMode
from aiogram.types import Message


def validate_username(username: str) -> Optional[str]:
    if not username or not username.strip():
        return None

    username = username.strip()
    if username.startswith("@"):
        username = username[1:]

    if not re.match(r"^[a-zA-Z0-9_]{5,32}$", username):
        return None

    return username


async def get_valid_username(message: Message) -> str | None:
    """
    Извлекает и валидирует username из сообщения.
    """
    username = extract_username(message.text)
    if username is None:
        await message.answer(
            text=(
                "Некорректно введена команда! \n"
                "Формат: <code>/add_moderator @username</code>"
            ),
            parse_mode=ParseMode.HTML,
        )
        return None

    username = validate_username(username=username)
    if username is None:
        await message.answer(
            text="Указан некорректный username. Проверьте формат и попробуйте снова.",
            parse_mode=ParseMode.HTML,
        )
        return None

    return username


def extract_username(text: str) -> str | None:
    """
    Извлекает username из текста команды.
    """
    segments = text.split(" ")
    if len(segments) > 1:
        username = segments[-1].strip()
        return username if username.startswith("@") else f"@{username}"
    return None
