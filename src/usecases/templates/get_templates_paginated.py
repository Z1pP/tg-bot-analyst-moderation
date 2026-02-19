"""Use case: пагинированный список шаблонов по категории, чату или глобальные."""

import logging
from typing import List, Tuple

from dto.template_dto import GetTemplatesPaginatedDTO
from models import MessageTemplate
from services.templates import TemplateService

logger = logging.getLogger(__name__)


class GetTemplatesPaginatedUseCase:
    """Возвращает страницу шаблонов и общее количество по фильтру (категория/чат/глобальные)."""

    def __init__(self, template_service: TemplateService) -> None:
        self._template_service = template_service

    async def execute(
        self, dto: GetTemplatesPaginatedDTO
    ) -> Tuple[List[MessageTemplate], int]:
        """
        Получает шаблоны с пагинацией.
        Фильтр: category_id > chat_id > глобальные.

        Returns:
            (список шаблонов, общее количество)
        """
        if dto.category_id is not None:
            templates = await self._template_service.get_by_category(
                category_id=dto.category_id,
                page=dto.page,
                page_size=dto.page_size,
            )
            total_count = await self._template_service.get_count_by_category(
                category_id=dto.category_id
            )
        elif dto.chat_id is not None:
            templates = await self._template_service.get_chat_templates_paginated(
                chat_id=dto.chat_id,
                page=dto.page,
                page_size=dto.page_size,
            )
            total_count = await self._template_service.get_chat_templates_count(
                chat_id=dto.chat_id
            )
        else:
            templates = await self._template_service.get_global_templates_paginated(
                page=dto.page,
                page_size=dto.page_size,
            )
            total_count = await self._template_service.get_global_templates_count()

        return templates, total_count
