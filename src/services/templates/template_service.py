from typing import List, Optional

from models import MessageTemplate
from repositories import MessageTemplateRepository
from services.caching import ICache


class TemplateService:
    """Сервис для работы с шаблона сообщений"""

    def __init__(self, template_repository: MessageTemplateRepository, cache: ICache):
        self._template_repository = template_repository
        self._cache = cache

    async def get_by_category(
        self,
        category_id: int,
        page: int = 1,
        page_size: int = 5,
    ) -> List[MessageTemplate]:
        """Получает список шаблонов по категории с пагинацией и кешированием"""
        cache_key = f"tpl:cat:{category_id}:page:{page}"
        cached = await self._cache.get(cache_key)
        if cached is not None:
            return cached

        offset = (page - 1) * page_size
        templates = list(
            await self._template_repository.get_templates_paginated(
                category_id=category_id,
                limit=page_size,
                offset=offset,
            )
        )
        await self._cache.set(cache_key, templates, ttl=3600)  # Кешируем на 1 час
        return templates

    async def invalidate_category_cache(self, category_id: int) -> None:
        """Инвалидирует весь кеш для конкретной категории"""
        # Так как мы не знаем точно сколько страниц, можем либо очистить по шаблону
        # либо (проще для начала) очистить первые N страниц
        for page in range(1, 11):  # Инвалидируем первые 10 страниц
            await self._cache.delete(f"tpl:cat:{category_id}:page:{page}")

    async def get_count(self) -> int:
        """Получает общее количество шаблонов"""
        return await self._template_repository.get_templates_count()

    async def get_count_by_category(self, category_id: int) -> int:
        """Получает количество шаблонов по категории"""
        return await self._template_repository.get_templates_count(
            category_id=category_id,
        )

    async def get_global_templates_paginated(
        self,
        page: int = 1,
        page_size: int = 5,
    ) -> List[MessageTemplate]:
        """Получает глобальные шаблоны с пагинацией"""
        offset = (page - 1) * page_size
        return await self._template_repository.get_templates_paginated(
            offset=offset, limit=page_size, global_only=True
        )

    async def get_global_templates_count(self) -> int:
        """Получает количество глобальных шаблонов"""
        return await self._template_repository.get_templates_count(global_only=True)

    async def get_chat_templates_paginated(
        self,
        chat_id: int,
        page: int = 1,
        page_size: int = 5,
    ) -> List[MessageTemplate]:
        """Получает шаблоны для конкретного чата с пагинацией"""
        offset = (page - 1) * page_size
        return await self._template_repository.get_templates_paginated(
            chat_id=chat_id, offset=offset, limit=page_size
        )

    async def get_chat_templates_count(self, chat_id: int) -> int:
        """Получает количество шаблонов для конкретного чата"""
        return await self._template_repository.get_templates_count(chat_id=chat_id)

    async def get_template_by_id(self, template_id: int) -> Optional[MessageTemplate]:
        """Получает шаблон по ID."""
        return await self._template_repository.get_template_by_id(template_id)

    async def get_template_and_increase_usage(
        self, template_id: int, chat_id: str
    ) -> Optional[MessageTemplate]:
        """Получает шаблон и увеличивает счетчик использования."""
        return await self._template_repository.get_template_and_increase_usage_count(
            template_id=template_id, chat_id=chat_id
        )

    async def get_templates_by_query(self, query: str) -> List[MessageTemplate]:
        """Ищет шаблоны по запросу."""
        return await self._template_repository.get_templates_by_query(query=query)

    async def delete_template(self, template_id: int) -> bool:
        """Удаляет шаблон и инвалидирует кеш."""
        template = await self._template_repository.get_template_by_id(template_id)
        if not template:
            return False

        category_id = template.category_id
        result = await self._template_repository.delete_template(template_id)
        if result and category_id:
            await self.invalidate_category_cache(category_id)
        return result

    async def update_template_title(self, template_id: int, new_title: str) -> bool:
        """Обновляет название шаблона и инвалидирует кеш."""
        success = await self._template_repository.update_template_title(
            template_id, new_title
        )
        if success:
            template = await self._template_repository.get_template_by_id(template_id)
            if template and template.category_id:
                await self.invalidate_category_cache(template.category_id)
        return success
