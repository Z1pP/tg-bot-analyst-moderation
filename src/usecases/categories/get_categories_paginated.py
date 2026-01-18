import logging
from typing import List, Tuple

from models import TemplateCategory
from services import CategoryService

logger = logging.getLogger(__name__)


class GetCategoriesPaginatedUseCase:
    def __init__(self, category_service: CategoryService):
        self._category_service = category_service

    async def execute(
        self, limit: int, offset: int
    ) -> Tuple[List[TemplateCategory], int]:
        """
        Получает категории с пагинацией.

        Args:
            limit: Количество категорий на странице
            offset: Смещение

        Returns:
            Tuple[List[TemplateCategory], int]: Категории и общее количество
        """
        try:
            categories = await self._category_service.get_categories_paginated(
                limit=limit, offset=offset
            )
            total_count = await self._category_service.get_categories_count()

            logger.debug(f"Получено {len(categories)} категорий из {total_count}")
            return categories, total_count

        except Exception as e:
            logger.error(f"Ошибка при получении категорий: {e}")
            raise
