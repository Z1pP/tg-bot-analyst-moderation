import logging
from typing import Optional

from dto import CategoryDTO
from exceptions.category import CategoryNotFoundError
from repositories import TemplateCategoryRepository

logger = logging.getLogger(__name__)


class GetCategoryByIdUseCase:
    def __init__(self, category_repository: TemplateCategoryRepository):
        self.category_repository = category_repository

    async def execute(self, category_id: int) -> Optional[CategoryDTO]:
        """
        Получает категорию по ID.

        Args:
            category_id: ID категории

        Returns:
            Optional[CategoryDTO]: DTO категории или None
        """
        category = await self.category_repository.get_category_by_id(category_id)

        if not category:
            logger.warning(
                f"Попытка удалить несуществующую категорию (ID={category_id})"
            )
            raise CategoryNotFoundError()

        return CategoryDTO.from_model(category)
