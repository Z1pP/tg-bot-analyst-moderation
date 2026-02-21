"""Вспомогательные функции для кеша шаблонов."""

from services.caching import ICache

# Количество страниц категории, инвалидируемых при изменении (достаточно для UI)
CATEGORY_CACHE_PAGES = 10


async def invalidate_category_pages(cache: ICache, category_id: int) -> None:
    """
    Инвалидирует кеш страниц шаблонов по категории.
    Используется при создании/обновлении/удалении шаблонов в категории.
    """
    for page in range(1, CATEGORY_CACHE_PAGES + 1):
        await cache.delete(f"tpl:cat:{category_id}:page:{page}")
