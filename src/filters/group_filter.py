from typing import Optional

from aiogram.filters import Filter
from aiogram.types import CallbackQuery, Message

from constants.enums import ChatType


class GroupTypeFilter(Filter):
    def __init__(self, chat_type: Optional[list[ChatType]] = None):
        self.chat_type = chat_type or [ChatType.GROUP, ChatType.SUPERGROUP]

    async def __call__(self, message: Message, *args, **kwds):
        return message.chat.type in self.chat_type


class ChatTypeFilter(Filter):
    def __init__(self, chat_type: Optional[list[ChatType]] = None):
        self.chat_type = chat_type or [ChatType.PRIVATE]

    async def __call__(self, event: Message | CallbackQuery, *args, **kwds):
        if isinstance(event, Message):
            return event.chat.type in self.chat_type
        elif isinstance(event, CallbackQuery):
            return event.message.chat.type in self.chat_type
        return False
