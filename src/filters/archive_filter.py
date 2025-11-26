import re

from aiogram.filters import Filter
from aiogram.types import Message

# Паттерн для поиска hash в формате ARCHIVE-{hash}
HASH_PATTERN = re.compile(r"ARCHIVE-([A-Za-z0-9_-]+)")


class ArchiveHashFilter(Filter):
    """Фильтр для проверки наличия hash привязки в сообщении."""

    async def __call__(self, message: Message) -> bool:
        """Проверяет наличие hash в тексте сообщения или подписи."""
        text = message.text or message.caption or ""
        if not text:
            return False
        return bool(HASH_PATTERN.search(text))
