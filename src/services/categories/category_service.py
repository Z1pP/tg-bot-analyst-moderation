from typing import List, Optional, Sequence

from models import TemplateCategory
from repositories import TemplateCategoryRepository
from services.caching import ICache


class CategoryService:
    """Сервис для работы с категориями шаблонов"""

    def __init__(self, category_repository: TemplateCategoryRepository, cache: ICache):
        self._category_repository = category_repository
        self._cache = cache

    async def get_categories(self) -> List[TemplateCategory]:
        """
        Получает список категорий из БД с проверкой кеша.
        """
        cache_key = "cat:all"
        categories = await self._cache.get(cache_key)
        if categories is not None:
            return categories

        categories = list(await self._category_repository.get_all_categories())
        await self._cache.set(cache_key, categories, ttl=86400)  # Кешируем на 1 день
        return categories

    async def get_category_by_id(self, category_id: int) -> Optional[TemplateCategory]:
        """Получает категорию по ID."""
        return await self._category_repository.get_category_by_id(category_id)

    async def create_category(self, name: str) -> Optional[TemplateCategory]:
        """Создает новую категорию и инвалидирует кеш."""
        category = await self._category_repository.create_category(name=name)
        if category:
            await self._cache.delete("cat:all")
        return category

    async def update_category_name(
        self, category_id: int, new_name: str
    ) -> TemplateCategory:
        """Обновляет название категории и инвалидирует кеш."""
        category = await self._category_repository.update_category_name(
            category_id=category_id, new_name=new_name
        )
        if category:
            await self._cache.delete("cat:all")
        return category

    async def delete_category(self, category_id: int) -> None:
        """Удаляет категорию и инвалидирует кеш."""
        await self._category_repository.delete_category(category_id=category_id)
        await self._cache.delete("cat:all")

    async def get_categories_paginated(
        self, limit: int = 5, offset: int = 0
    ) -> Sequence[TemplateCategory]:
        """Получает категории с пагинацией."""
        return await self._category_repository.get_categories_paginated(
            limit=limit, offset=offset
        )

    async def get_categories_count(self) -> int:
        """Получает общее количество категорий."""
        return await self._category_repository.get_categories_count()
