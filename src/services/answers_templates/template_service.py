from typing import List

from models import MessageTemplate
from repositories import MessageTemplateRepository


class TemplateService:
    """Сервис для работы с шаблона сообщений"""

    def __init__(self, template_repository: MessageTemplateRepository):
        self._template_repository = template_repository

    async def get_by_category(
        self,
        category_id: int,
        page: int = 1,
        page_size: int = 5,
    ) -> List[MessageTemplate]:
        """Получает список шаблонов по категории с пагинацией"""

        offset = (page - 1) * page_size
        return await self._template_repository.get_templates_by_category_paginated(
            category_id=category_id,
            limit=page_size,
            offset=offset,
        )

    async def get_by_page(
        self,
        page: int = 1,
        page_size: int = 5,
    ) -> List[MessageTemplate]:
        """Получает шаблоны с пагинацией"""

        offset = (page - 1) * page_size
        return await self.repo.get_templates_paginated(
            limit=page_size,
            offset=offset,
        )

    async def get_count(self) -> int:
        """Получает общее количество шаблонов"""

        return await self._template_repository.get_templates_count()

    async def get_count_by_category(self, category_id: int) -> int:
        """Получает количество шаблонов по категории"""

        return await self._template_repository.get_templates_count_by_category(
            category_id=category_id,
        )
