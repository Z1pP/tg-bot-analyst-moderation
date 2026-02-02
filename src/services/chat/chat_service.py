from datetime import time
from typing import Optional

from models import ChatSession
from repositories import ChatRepository
from services.caching import ICache


class ChatService:
    """
    Сервис для управления настройками чатов и их сессиями.

    Обеспечивает:
    - Поиск и создание чатов
    - Привязку архивных каналов
    - Управление настройками (антибот, приветствие, рабочие часы)
    - Автоматическую инвалидацию и обновление кеша
    """

    def __init__(self, chat_repository: ChatRepository, cache: ICache):
        self._chat_repository = chat_repository
        self._cache = cache

    async def get_chat(
        self,
        chat_tgid: str,
        title: Optional[str] = None,
    ) -> Optional[ChatSession]:
        """
        Получает информацию о чате по его Telegram ID.
        Если название изменилось, обновляет его в БД и кеше.

        Args:
            chat_tgid: Telegram ID чата
            title: Текущее название чата (для синхронизации)

        Returns:
            Объект ChatSession или None
        """
        cache_key = f"chat:tg_id:{chat_tgid}"
        chat = await self._cache.get(cache_key)
        if chat:
            if title and chat.title != title:
                chat = await self._chat_repository.update_chat(
                    chat_id=chat.id,
                    title=title,
                )
                await self._cache.set(cache_key, chat)
                await self._cache.set(f"chat:archive:{chat_tgid}", chat)
            return chat

        chat = await self._chat_repository.get_chat_by_tgid(chat_tgid)
        if chat:
            if title and chat.title != title:
                chat = await self._chat_repository.update_chat(
                    chat_id=chat.id,
                    title=title,
                )
            await self._cache.set(cache_key, chat)
            await self._cache.set(f"chat:archive:{chat_tgid}", chat)

        return chat or None

    async def create_chat(self, chat_id: str, title: str) -> ChatSession:
        """
        Создает новую запись чата в БД и кеширует её.

        Args:
            chat_id: Telegram ID чата
            title: Название чата

        Returns:
            Созданный объект ChatSession
        """
        chat = await self._chat_repository.create_chat(
            chat_id=str(chat_id), title=title
        )

        if chat:
            await self._cache.set(f"chat:tg_id:{chat_id}", chat)
            await self._cache.set(f"chat:archive:{chat_id}", chat)
        return chat

    async def get_or_create(
        self, chat_tgid: str, title: Optional[str] = None
    ) -> ChatSession:
        """
        Получает существующий чат или создает новый, если он не найден.

        Args:
            chat_id: Telegram ID чата
            title: Название чата

        Returns:
            Объект ChatSession
        """
        chat = await self.get_chat(chat_tgid=chat_tgid, title=title)
        if chat:
            return chat

        new_chat = await self.create_chat(chat_tgid, title)

        return new_chat

    async def _update_and_sync_cache(
        self, chat_id: int, update_func, **kwargs
    ) -> Optional[ChatSession]:
        """
        Вспомогательный метод для обновления данных чата в БД и синхронизации кеша.

        Args:
            chat_id: ID чата из БД
            update_func: Метод репозитория для обновления
            **kwargs: Аргументы для update_func

        Returns:
            Обновленный объект ChatSession или None
        """
        current_chat = await self._chat_repository.get_chat_by_id(chat_id)
        if current_chat:
            await self._cache.delete(f"chat:tg_id:{current_chat.chat_id}")
            await self._cache.delete(f"chat:archive:{current_chat.chat_id}")

        chat = await update_func(chat_id=chat_id, **kwargs)
        if chat:
            await self._cache.set(f"chat:tg_id:{chat.chat_id}", chat)
            await self._cache.set(f"chat:archive:{chat.chat_id}", chat)
        return chat

    async def get_chat_with_archive(
        self,
        chat_tgid: Optional[str] = None,
        chat_id: Optional[int] = None,
    ) -> Optional[ChatSession]:
        """
        Получает чат и его архивный чат если есть.
        Сначала проверяет кеш, затем БД.
        """
        if not chat_tgid and not chat_id:
            raise ValueError("Необходимо передать chat_tgid или chat_id")

        # Пробуем получить из кеша
        if chat_tgid:
            cache_key = f"chat:archive:{chat_tgid}"
            chat = await self._cache.get(cache_key)
            if chat:
                return chat

        # Если в кеше нет или ищем по id, загружаем из репозитория
        if chat_id:
            chat = await self._chat_repository.get_chat_by_id(chat_id=chat_id)
        else:
            chat = await self._chat_repository.get_chat_by_tgid(chat_tgid)

        # Кешируем результат если он найден и искали по tgid
        if chat and chat_tgid:
            await self._cache.set(f"chat:archive:{chat_tgid}", chat)
            await self._cache.set(f"chat:tg_id:{chat_tgid}", chat)

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
            await self._cache.set(f"chat:tg_id:{work_chat.chat_id}", work_chat)
            await self._cache.set(f"chat:archive:{work_chat.chat_id}", work_chat)
            # Обновляем кеш для архивного чата если он был создан
            if work_chat.archive_chat_id:
                archive_chat = await self._chat_repository.get_chat_by_tgid(
                    work_chat.archive_chat_id
                )
                if archive_chat:
                    await self._cache.set(
                        f"chat:tg_id:{archive_chat.chat_id}", archive_chat
                    )
                    await self._cache.set(
                        f"chat:archive:{archive_chat.chat_id}", archive_chat
                    )

        return work_chat

    async def toggle_antibot(self, chat_id: int) -> Optional[bool]:
        """
        Переключает статус антибота для чата и обновляет кеш.

        Args:
            chat_id: ID чата из БД

        Returns:
            Новое состояние или None
        """
        chat = await self._update_and_sync_cache(
            chat_id=chat_id, update_func=self._chat_repository.toggle_antibot
        )
        return chat.is_antibot_enabled if chat else None

    async def toggle_show_welcome_text(self, chat_id: int) -> Optional[bool]:
        """
        Переключает показ приветственного текста для чата и обновляет кеш.

        Args:
            chat_id: ID чата из БД

        Returns:
            Новое состояние или None
        """
        chat = await self._update_and_sync_cache(
            chat_id=chat_id,
            update_func=self._chat_repository.toggle_show_welcome_text,
        )
        return chat.show_welcome_text if chat else None

    async def toggle_auto_delete_welcome_text(self, chat_id: int) -> Optional[bool]:
        """
        Переключает автоудаление приветственного текста для чата и обновляет кеш.

        Args:
            chat_id: ID чата из БД

        Returns:
            Новое состояние или None
        """
        chat = await self._update_and_sync_cache(
            chat_id=chat_id,
            update_func=self._chat_repository.toggle_auto_delete_welcome_text,
        )
        return chat.auto_delete_welcome_text if chat else None

    async def update_welcome_text(
        self, chat_id: int, welcome_text: str
    ) -> Optional[ChatSession]:
        """
        Обновляет приветственный текст чата и обновляет кеш.

        Args:
            chat_id: ID чата из БД
            welcome_text: Новый текст приветствия

        Returns:
            Обновленный объект ChatSession или None
        """
        return await self._update_and_sync_cache(
            chat_id=chat_id,
            update_func=self._chat_repository.update_welcome_text,
            welcome_text=welcome_text,
        )

    async def update_work_hours(
        self,
        chat_id: int,
        start_time: Optional[time] = None,
        end_time: Optional[time] = None,
        tolerance: Optional[int] = None,
        breaks_time: Optional[int] = None,
    ) -> Optional[ChatSession]:
        """
        Обновляет рабочие часы чата и обновляет кеш.

        Args:
            chat_id: ID чата из БД
            start_time: Время начала работы
            end_time: Время окончания работы
            tolerance: Допустимое отклонение

        Returns:
            Обновленный объект ChatSession или None
        """
        return await self._update_and_sync_cache(
            chat_id=chat_id,
            update_func=self._chat_repository.update_work_hours,
            start_time=start_time,
            end_time=end_time,
            tolerance=tolerance,
            breaks_time=breaks_time,
        )
