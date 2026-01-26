from typing import Callable, Dict, Iterable, List, TypeVar

T = TypeVar("T")
K = TypeVar("K")


def group_by(items: Iterable[T], key: Callable[[T], K]) -> Dict[K, List[T]]:
    """
    Группирует элементы по ключу.

    Args:
        items: Итерируемая коллекция элементов.
        key: Функция получения ключа группировки.

    Returns:
        Словарь, где ключ — результат key(item), значение — список элементов.
    """
    grouped: Dict[K, List[T]] = {}
    for item in items:
        grouped.setdefault(key(item), []).append(item)
    return grouped
