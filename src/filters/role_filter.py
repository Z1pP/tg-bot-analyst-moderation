from typing import Optional

from aiogram.filters import Filter
from aiogram.types import Message

from config import settings


class IsAdminFilter(Filter):
    def __init__(self, admins: Optional[list[str]] = None):
        self._admins = admins or settings.ADMINS_LIST

    async def __call__(self, message: Message, *args, **kwds):
        return message.from_user.username in self._admins
