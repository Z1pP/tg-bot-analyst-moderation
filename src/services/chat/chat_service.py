from typing import List, Optional

from models import ChatSession
from repositories import ChatRepository
from services.caching import ICache


class ChatService:
    def __init__(self, chat_repository: ChatRepository, cache: ICache):
        self._chat_repository = chat_repository
        self._cache = cache

    async def get_chat(self, title: str) -> ChatSession:
        chat = await self._cache.get(title)
        if chat:
            return chat

        chat = await self._chat_repository.get_chat_by_title(title)
        if chat:
            await self._cache.set(title, chat)

        return chat

    async def create_chat(self, chat_id: str, title: str) -> ChatSession:
        chat = await self._chat_repository.create_chat(
            chat_id=str(chat_id), title=title
        )

        if chat:
            await self._cache.set(title, chat)
        return chat

    async def get_or_create_chat(self, chat_id: str, title: str) -> ChatSession:
        chat = await self.get_chat(title)
        if chat:
            return chat

        return await self.create_chat(chat_id, title)

    async def get_archive_chats(
        self,
        source_chat_title: str,
    ) -> Optional[List[ChatSession]]:
        return await self._chat_repository.get_archive_chats(
            source_chat_title=source_chat_title,
        )
