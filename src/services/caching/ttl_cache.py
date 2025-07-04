from typing import Optional, TypeVar

from cachetools import TTLCache

from .base import ICache

T = TypeVar("T")


class TTLEntityCache(ICache):
    """
    Реализация кеша с временем жизни (TTL) на основе cachetools.TTLCache.
    """

    def __init__(self, maxsize: int = 100, ttl: int = 600):
        """
        Инициализирует кеш с указанным размером и временем жизни.

        Args:
            maxsize: Максимальный размер кеша
            ttl: Время жизни элементов в секундах
        """
        self._cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def get(self, key: str) -> Optional[T]:
        """
        Получает значение из кеша по ключу.

        Args:
            key: Ключ для поиска в кеше

        Returns:
            Значение из кеша или None, если ключ не найден
        """
        try:
            return self._cache.get(key)
        except Exception:
            return None

    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """
        Устанавливает значение в кеш по ключу.

        Args:
            key: Ключ для сохранения в кеше
            entity: Значение для сохранения
            ttl: Время жизни в секундах (игнорируется в этой реализации)
        """
        try:
            self._cache[key] = value
        except Exception:
            pass

    def delete(self, key: str) -> bool:
        """
        Удаляет значение из кеша по ключу.

        Args:
            key: Ключ для удаления

        Returns:
            True, если значение было удалено, иначе False
        """
        try:
            if key in self._cache:
                del self._cache[key]
                return True
        except Exception:
            pass
        return False

    def clear(self) -> None:
        """
        Очищает весь кеш.
        """
        try:
            self._cache.clear()
        except Exception:
            pass
