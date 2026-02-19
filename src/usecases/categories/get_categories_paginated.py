import logging
from typing import List, Tuple

from dto import GetCategoriesPaginatedDTO
from models import TemplateCategory
from services import CategoryService

logger = logging.getLogger(__name__)


class GetCategoriesPaginatedUseCase:
    """Use case: пагинированный список категорий шаблонов."""

    def __init__(self, category_service: CategoryService) -> None:
        self._category_service = category_service

    async def execute(
        self, dto: GetCategoriesPaginatedDTO
    ) -> Tuple[List[TemplateCategory], int]:
        """
        Получает категории с пагинацией.

        Args:
            dto: limit и offset.

        Returns:
            Кортеж (список категорий, общее количество).
        """
        categories = await self._category_service.get_categories_paginated(
            limit=dto.limit, offset=dto.offset
        )
        total_count = await self._category_service.get_categories_count()
        logger.debug("Получено %s категорий из %s", len(categories), total_count)
        return list(categories), total_count
