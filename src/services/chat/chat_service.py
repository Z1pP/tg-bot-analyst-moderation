import logging
from collections.abc import Awaitable, Callable
from datetime import time
from typing import Any, Optional

from cachetools import TTLCache
from sqlalchemy.exc import IntegrityError

from dto.chat_dto import ChatSessionCacheDTO
from exceptions import DatabaseException
from models import ChatSession, ChatSettings
from repositories import ChatRepository
from services.caching import ICache

logger = logging.getLogger(__name__)


class ChatService:
    """
    Сервис для управления настройками чатов и их сессиями.

    Обеспечивает:
    - Поиск и создание чатов
    - Привязку архивных каналов
    - Управление настройками (антибот, приветствие, рабочие часы)
    - Автоматическую инвалидацию и обновление кеша
    """

    def __init__(
        self,
        chat_repository: ChatRepository,
        cache: ICache,
    ) -> None:
        self._chat_repository = chat_repository
        self._cache = cache
        self._archive_chat_cache: TTLCache = TTLCache(maxsize=200, ttl=300)

    def _materialize_chat_from_cache_dto(
        self, data: ChatSessionCacheDTO
    ) -> ChatSession:
        """Восстанавливает отсоединённые ORM-объекты для чтения (свойства без lazy load)."""
        kw: dict = {
            "chat_id": data.id,
            "start_time": data.start_time,
            "end_time": data.end_time,
            "tolerance": data.tolerance,
            "breaks_time": data.breaks_time,
            "is_antibot_enabled": data.is_antibot_enabled,
            "is_auto_moderation_enabled": data.is_auto_moderation_enabled,
            "welcome_text": data.welcome_text,
            "auto_delete_welcome_text": data.auto_delete_welcome_text,
            "show_welcome_text": data.show_welcome_text,
        }
        if data.settings_id is not None:
            kw["id"] = data.settings_id
        settings = ChatSettings(**kw)
        chat = ChatSession(
            id=data.id,
            chat_id=data.chat_id,
            title=data.title,
            archive_chat_id=data.archive_chat_id,
        )
        settings.chat = chat
        chat.settings = settings
        return chat

    async def _set_chat_cache(self, chat: ChatSession) -> None:
        """Пишет в Redis плоский DTO; in-memory — только полный ORM из БД (есть archive_chat в __dict__)."""
        payload = ChatSessionCacheDTO.from_chat_session(chat)
        await self._cache.set(f"chat:tg_id:{chat.chat_id}", payload)
        await self._cache.set(f"chat:archive:{chat.chat_id}", payload)
        if "archive_chat" in chat.__dict__:
            self._archive_chat_cache[chat.chat_id] = chat

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
        cached = await self._cache.get(cache_key)
        chat: Optional[ChatSession] = None
        if cached is not None:
            if isinstance(cached, ChatSessionCacheDTO):
                chat = self._materialize_chat_from_cache_dto(cached)
            elif isinstance(cached, ChatSession):
                logger.debug(
                    "chat cache: устаревший pickle ORM для %s — инвалидация ключа",
                    chat_tgid,
                )
                await self._cache.delete(cache_key)
            else:
                logger.warning(
                    "chat cache: неожиданный тип %s для %s — инвалидация",
                    type(cached),
                    chat_tgid,
                )
                await self._cache.delete(cache_key)

        if chat:
            if title and chat.title != title:
                updated_chat = await self._chat_repository.update_chat(
                    chat_id=chat.id,
                    title=title,
                )
                if updated_chat:
                    chat = updated_chat
                    await self._set_chat_cache(chat)
            return chat

        chat = await self._chat_repository.get_chat_by_tgid(chat_tgid)
        if chat:
            if title and chat.title != title:
                updated_chat = await self._chat_repository.update_chat(
                    chat_id=chat.id,
                    title=title,
                )
                if updated_chat:
                    chat = updated_chat
            await self._set_chat_cache(chat)
        return chat or None

    async def create_chat(self, chat_tgid: str, title: str) -> ChatSession:
        """
        Создает новую запись чата в БД и кеширует её.

        Args:
            chat_tgid: Telegram ID чата
            title: Название чата

        Returns:
            Созданный объект ChatSession
        """
        chat = await self._chat_repository.create_chat(
            chat_id=str(chat_tgid), title=title
        )
        if chat:
            await self._set_chat_cache(chat)
        return chat

    async def get_or_create(
        self, chat_tgid: str, title: Optional[str] = None
    ) -> ChatSession:
        """
        Получает существующий чат или создает новый, если он не найден.

        Args:
            chat_tgid: Telegram ID чата
            title: Название чата

        Returns:
            Объект ChatSession
        """
        chat = await self.get_chat(chat_tgid=chat_tgid, title=title)
        if chat:
            return chat

        try:
            return await self.create_chat(chat_tgid, title)
        except DatabaseException as e:
            if isinstance(e.__cause__, IntegrityError):
                logger.warning(
                    "Race condition: чат с chat_tgid=%s создан параллельно",
                    chat_tgid,
                )
                chat = await self.get_chat(chat_tgid=chat_tgid, title=title)
                if chat:
                    return chat
            raise

    async def update_chat_title(
        self, chat_id: int, title: str
    ) -> Optional[ChatSession]:
        """
        Обновляет title чата в БД и синхронизирует кеш.
        chat_id — id записи в БД (ChatSession.id).
        """
        return await self._update_and_sync_cache(
            chat_id=chat_id,
            update_func=self._chat_repository.update_chat,
            title=title,
        )

    async def _update_and_sync_cache(
        self,
        chat_id: int,
        update_func: Callable[..., Awaitable[Optional[ChatSession]]],
        **kwargs: Any,
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
        chat = await update_func(chat_id=chat_id, **kwargs)
        if chat:
            await self._set_chat_cache(chat)
        return chat

    async def get_chat_with_archive(
        self,
        chat_tgid: Optional[str] = None,
        chat_id: Optional[int] = None,
    ) -> Optional[ChatSession]:
        """
        Получает чат и его архивный чат если есть.
        Использует in-memory кеш (без pickle) — ORM relationships остаются работоспособными.

        Примечание: in-memory кеш проверяется только при вызове с chat_tgid.
        При вызове с chat_id (DB id) кеш не проверяется — запрос идёт в БД.
        Для производительности предпочтительно передавать chat_tgid.
        """
        if not chat_tgid and not chat_id:
            raise ValueError("Необходимо передать chat_tgid или chat_id")

        # In-memory кеш (без Redis — pickle ломает archive_chat lazy load)
        if chat_tgid:
            chat = self._archive_chat_cache.get(chat_tgid)
            if chat:
                return chat

        # Загрузка из репозитория
        if chat_id:
            chat = await self._chat_repository.get_chat_by_id(chat_id=chat_id)
        else:
            chat = await self._chat_repository.get_chat_by_tgid(chat_tgid)

        if chat:
            tgid = chat_tgid or chat.chat_id
            self._archive_chat_cache[tgid] = chat

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
            await self._set_chat_cache(work_chat)
            if work_chat.archive_chat_id:
                archive_chat = await self._chat_repository.get_chat_by_tgid(
                    work_chat.archive_chat_id
                )
                if archive_chat:
                    await self._set_chat_cache(archive_chat)
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

    async def toggle_auto_moderation(self, chat_id: int) -> Optional[bool]:
        """
        Переключает автомодерацию для чата и обновляет кеш.

        Args:
            chat_id: ID чата из БД

        Returns:
            Новое состояние или None
        """
        chat = await self._update_and_sync_cache(
            chat_id=chat_id,
            update_func=self._chat_repository.toggle_auto_moderation,
        )
        return chat.is_auto_moderation_enabled if chat else None

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
