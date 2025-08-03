import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware, types

DataType = dict[str, Any]
AlbumMessages = list[types.Message]


class AlbumMiddleware(BaseMiddleware):
    """
    Middleware для обработки медиа-групп (альбомов) в Aiogram.

    Собирает все сообщения из одной медиа-группы и передает их вместе
    в обработчик только после получения всех сообщений группы.

    Attributes:
        timeout (float): Время ожидания между сообщениями группы в секундах
        album_messages (defaultdict): Словарь для хранения сообщений по группам
    """

    def __init__(self, timeout: float = 0.1):
        """
        Инициализирует middleware с указанным таймаутом.

        Args:
            timeout (float): Время ожидания между сообщениями группы в секундах
        """
        self.timeout = timeout
        self.album_messages = defaultdict[str, AlbumMessages](list)

    def get_count(self, message: types.Message) -> int:
        """
        Возвращает количество сообщений в группе.

        Args:
            message (types.Message): Сообщение с media_group_id

        Returns:
            int: Количество сообщений в группе
        """
        return len(self.album_messages[message.media_group_id])

    def store_album_message(self, message: types.Message) -> int:
        """
        Сохраняет сообщение в соответствующей группе.

        Args:
            message (types.Message): Сообщение для сохранения

        Returns:
            int: Новое количество сообщений в группе
        """
        self.album_messages[message.media_group_id].append(message)
        return self.get_count(message)

    def get_result_messages(self, message: types.Message) -> AlbumMessages:
        """
        Извлекает и сортирует все сообщения группы.

        Args:
            message (types.Message): Сообщение с media_group_id

        Returns:
            AlbumMessages: Отсортированный список сообщений группы
        """
        album_messages = self.album_messages.pop(message.media_group_id)
        album_messages.sort(key=lambda m: m.message_id)
        return album_messages

    async def __call__(
        self,
        handler: Callable[[types.Message, DataType], Awaitable],
        event: types.Message,
        data: DataType,
    ):
        """
        Обрабатывает вызов middleware.

        Если сообщение не является частью медиа-группы, передает его напрямую.
        Иначе собирает все сообщения группы и передает их вместе.

        Args:
            handler: Следующий обработчик в цепочке
            event: Входящее сообщение
            data: Данные контекста

        Returns:
            Результат выполнения обработчика
        """
        if event.media_group_id is None:
            return await handler(event, data)

        count = self.store_album_message(event)
        await asyncio.sleep(self.timeout)

        if self.get_count(event) != count:
            return

        data.update(album_messages=self.get_result_messages(event))
        return await handler(event, data)
