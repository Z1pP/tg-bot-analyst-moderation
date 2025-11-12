import logging
from typing import Optional

from dto import CategoryDTO
from exceptions.category import CategoryNotFoundError
from repositories import TemplateCategoryRepository

logger = logging.getLogger(__name__)


class UpdateCategoryNameUseCase:
    def __init__(self, category_repository: TemplateCategoryRepository):
        self.category_repository = category_repository

    async def execute(self, category_id: int, new_name: str) -> Optional[CategoryDTO]:
        """
        Обновляет название категории.

        Args:
            category_id: ID категории
            new_name: Новое название

        Returns:
            Optional[CategoryDTO]: DTO категории или None
        """
        category = await self.category_repository.get_category_by_id(category_id)

        if not category:
            logger.warning(
                f"Попытка изменить несуществующую категорию (ID={category_id})"
            )
            raise CategoryNotFoundError()

        updated_category = await self.category_repository.update_category_name(
            category_id, new_name
        )
        return CategoryDTO.from_model(updated_category)
