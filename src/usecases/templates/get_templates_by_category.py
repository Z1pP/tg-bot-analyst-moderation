"""Use case: получение шаблонов по категории с пагинацией."""

import logging
from typing import List, Tuple

from dto.template_dto import GetTemplatesByCategoryDTO
from models import MessageTemplate
from services.templates import TemplateService

logger = logging.getLogger(__name__)


class GetTemplatesByCategoryUseCase:
    """Возвращает список шаблонов по категории и общее количество."""

    def __init__(self, template_service: TemplateService) -> None:
        self._template_service = template_service

    async def execute(
        self, dto: GetTemplatesByCategoryDTO
    ) -> Tuple[List[MessageTemplate], int]:
        """
        Получает шаблоны по категории.

        Returns:
            (список шаблонов, общее количество)
        """
        templates = await self._template_service.get_by_category(
            category_id=dto.category_id,
            page=dto.page,
            page_size=dto.page_size,
        )
        total_count = await self._template_service.get_count_by_category(
            category_id=dto.category_id
        )
        return templates, total_count
