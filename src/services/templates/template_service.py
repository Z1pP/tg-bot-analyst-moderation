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

    async def get_count(self) -> int:
        """Получает общее количество шаблонов"""

        return await self._template_repository.get_templates_count()

    async def get_count_by_category(self, category_id: int) -> int:
        """Получает количество шаблонов по категории"""

        return await self._template_repository.get_templates_count_by_category(
            category_id=category_id,
        )

    async def get_global_templates_paginated(
        self,
        page: int = 1,
        page_size: int = 5,
    ) -> List[MessageTemplate]:
        """Получает глобальные шаблоны с пагинацией"""
        offset = (page - 1) * page_size
        return await self._template_repository.get_global_templates_paginated(
            offset=offset, limit=page_size
        )

    async def get_global_templates_count(self) -> int:
        """Получает количество глобальных шаблонов"""
        return await self._template_repository.get_global_templates_count()

    async def get_chat_templates_paginated(
        self,
        chat_id: int,
        page: int = 1,
        page_size: int = 5,
    ) -> List[MessageTemplate]:
        """Получает шаблоны для конкретного чата с пагинацией"""
        offset = (page - 1) * page_size
        return await self._template_repository.get_chat_templates_paginated(
            chat_id=chat_id, offset=offset, limit=page_size
        )

    async def get_chat_templates_count(self, chat_id: int) -> int:
        """Получает количество шаблонов для конкретного чата"""
        return await self._template_repository.get_chat_templates_count(chat_id=chat_id)
