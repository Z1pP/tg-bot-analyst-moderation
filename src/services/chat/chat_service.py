from typing import Optional

from models import ChatSession
from repositories import ChatRepository
from services.caching import ICache


class ChatService:
    def __init__(self, chat_repository: ChatRepository, cache: ICache):
        self._chat_repository = chat_repository
        self._cache = cache

    async def get_chat(
        self,
        chat_tgid: str,
        title: Optional[str] = None,
    ) -> Optional[ChatSession]:
        chat = await self._cache.get(chat_tgid)
        if chat:
            if title and chat.title != title:
                chat = await self._chat_repository.update_chat(
                    chat_id=chat.id,
                    title=title,
                )
                await self._cache.set(chat_tgid, chat)
            return chat

        chat = await self._chat_repository.get_chat_by_tgid(chat_tgid)
        if chat:
            if title and chat.title != title:
                chat = await self._chat_repository.update_chat(
                    chat_id=chat.id,
                    title=title,
                )
            await self._cache.set(chat_tgid, chat)

        return chat or None

    async def create_chat(self, chat_id: str, title: str) -> ChatSession:
        chat = await self._chat_repository.create_chat(
            chat_id=str(chat_id), title=title
        )

        if chat:
            await self._cache.set(chat_id, chat)
        return chat

    async def get_or_create(self, chat_id: str, title: str) -> ChatSession:
        chat = await self.get_chat(chat_tgid=chat_id, title=title)
        if chat:
            return chat

        new_chat = await self.create_chat(chat_id, title)

        await self._cache.set(chat_id, new_chat)
        return new_chat

    async def get_chat_with_archive(
        self,
        chat_tgid: Optional[str] = None,
        chat_id: Optional[int] = None,
    ) -> Optional[ChatSession]:
        """Получает чат и его архивный чат если есть."""
        chat = None

        if not chat_tgid and not chat_id:
            raise ValueError("Необходимо передать chat_tgid или chat_id")

        if chat_id:
            chat = await self._chat_repository.get_chat_by_id(chat_id=chat_id)
        else:
            chat = await self.get_chat(chat_tgid=chat_tgid)

        return chat or None
