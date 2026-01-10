from datetime import time
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
        if not chat_tgid and not chat_id:
            raise ValueError("Необходимо передать chat_tgid или chat_id")

        # Всегда загружаем из репозитория с selectinload для archive_chat
        # чтобы избежать проблем с detached объектами из кеша
        if chat_id:
            chat = await self._chat_repository.get_chat_by_id(chat_id=chat_id)
        else:
            chat = await self._chat_repository.get_chat_by_tgid(chat_tgid)

        return chat or None

    async def bind_archive_chat(
        self,
        work_chat_id: int,
        archive_chat_tgid: str,
        archive_chat_title: Optional[str] = None,
    ) -> Optional[ChatSession]:
        """
        Привязывает архивный чат к рабочему.

        Args:
            work_chat_id: ID рабочего чата из БД
            archive_chat_tgid: Telegram ID архивного чата
            archive_chat_title: Название архивного чата (опционально)

        Returns:
            Обновленный рабочий чат или None
        """
        work_chat = await self._chat_repository.bind_archive_chat(
            work_chat_id=work_chat_id,
            archive_chat_tgid=archive_chat_tgid,
            archive_chat_title=archive_chat_title,
        )

        if work_chat:
            # Обновляем кеш для рабочего чата
            await self._cache.set(work_chat.chat_id, work_chat)
            # Обновляем кеш для архивного чата если он был создан
            if work_chat.archive_chat_id:
                archive_chat = await self._chat_repository.get_chat_by_tgid(
                    work_chat.archive_chat_id
                )
                if archive_chat:
                    await self._cache.set(archive_chat.chat_id, archive_chat)

        return work_chat

    async def toggle_antibot(self, chat_id: int) -> Optional[bool]:
        """
        Переключает статус антибота для чата и обновляет кеш.

        Args:
            chat_id: ID чата из БД

        Returns:
            Новое состояние или None
        """
        # Сначала получаем текущий чат, чтобы точно знать его Telegram ID (ключ в кеше)
        current_chat = await self._chat_repository.get_chat_by_id(chat_id)
        if current_chat:
            await self._cache.delete(current_chat.chat_id)

        new_state = await self._chat_repository.toggle_antibot(chat_id)
        if new_state is not None:
            # Обновляем объект в кеше
            chat = await self._chat_repository.get_chat_by_id(chat_id)
            if chat:
                await self._cache.set(chat.chat_id, chat)

        return new_state

    async def update_welcome_text(
        self, chat_id: int, welcome_text: str
    ) -> Optional[ChatSession]:
        """
        Обновляет приветственный текст чата и обновляет кеш.
        """
        current_chat = await self._chat_repository.get_chat_by_id(chat_id)
        if current_chat:
            await self._cache.delete(current_chat.chat_id)

        chat = await self._chat_repository.update_welcome_text(
            chat_id=chat_id, welcome_text=welcome_text
        )
        if chat:
            await self._cache.set(chat.chat_id, chat)
        return chat

    async def update_work_hours(
        self,
        chat_id: int,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        tolerance: Optional[int] = None,
    ) -> Optional[ChatSession]:
        """
        Обновляет рабочие часы чата и обновляет кеш.
        """
        current_chat = await self._chat_repository.get_chat_by_id(chat_id)
        if current_chat:
            await self._cache.delete(current_chat.chat_id)

        chat = await self._chat_repository.update_work_hours(
            chat_id=chat_id,
            start_time=start_time,
            end_time=end_time,
            tolerance=tolerance,
        )
        if chat:
            await self._cache.set(chat.chat_id, chat)
        return chat
