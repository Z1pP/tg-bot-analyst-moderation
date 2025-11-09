from typing import List, Optional

from models import ChatSession
from repositories import ChatRepository
from services.caching import ICache


class ChatService:
    def __init__(self, chat_repository: ChatRepository, cache: ICache):
        self._chat_repository = chat_repository
        self._cache = cache

    async def get_chat(self, chat_id: str, title: str = None) -> ChatSession:
        chat = await self._cache.get(chat_id)
        if chat:
            if title and chat.title != title:
                chat = await self._chat_repository.update_chat(
                    chat_id=chat.id,
                    title=title,
                )
                await self._cache.set(chat_id, chat)
            return chat

        chat = await self._chat_repository.get_chat_by_chat_id(chat_id)
        if chat:
            if title and chat.title != title:
                chat = await self._chat_repository.update_chat(
                    chat_id=chat.id,
                    title=title,
                )
            await self._cache.set(chat_id, chat)

        return chat

    async def create_chat(self, chat_id: str, title: str) -> ChatSession:
        chat = await self._chat_repository.create_chat(
            chat_id=str(chat_id), title=title
        )

        if chat:
            await self._cache.set(chat_id, chat)
        return chat

    async def get_or_create(self, chat_id: str, title: str) -> ChatSession:
        chat = await self.get_chat(chat_id=chat_id, title=title)
        if chat:
            return chat

        new_chat = await self.create_chat(chat_id, title)

        await self._cache.set(chat_id, new_chat)
        return new_chat

    async def get_archive_chats(
        self,
        source_chat_tgid: str,
    ) -> Optional[List[ChatSession]]:
        return await self._chat_repository.get_archive_chats(
            source_chat_tgid=source_chat_tgid,
        )
