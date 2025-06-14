from abc import ABC, abstractmethod
from typing import Optional, TypeVar

T = TypeVar("T")


class ICache(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[T]:
        """
        Получает значение из кеша по ключу.

        Args:
            key: Ключ для поиска в кеше

        Returns:
            Значение из кеша или None, если ключ не найден
        """
        pass

    @abstractmethod
    def set(self, key: str, value: T, ttl: Optional[int] = None) -> None:
        """
        Устанавливает значение в кеш по ключу.

        Args:
            key: Ключ для сохранения в кеше
            value: Значение для сохранения
            ttl: Время жизни в секундах (опционально)
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Удаляет значение из кеша по ключу.

        Args:
            key: Ключ для удаления

        Returns:
            True, если значение было удалено, иначе False
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Очищает весь кеш.
        """
        pass
