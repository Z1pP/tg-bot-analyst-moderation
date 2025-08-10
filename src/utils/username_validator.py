from typing import Optional

from aiogram.enums import ParseMode
from aiogram.types import Message


def parse_and_validate_username(text: str) -> Optional[str]:
    if not text or not text.strip():
        return None

    text = text.strip()
    if text.startswith("@"):
        text = text[1:]
        return text
    return None


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

    username = parse_and_validate_username(text=username)
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
