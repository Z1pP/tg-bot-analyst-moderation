import logging
from typing import Optional

from dto import CategoryDTO
from exceptions.category import CategoryNotFoundError
from repositories import TemplateCategoryRepository

logger = logging.getLogger(__name__)


class DeleteCategoryUseCase:
    """Use case для удаления категории шаблонов."""

    def __init__(self, category_repository: TemplateCategoryRepository):
        self._category_repository = category_repository

    async def execute(self, category_id: int) -> Optional[CategoryDTO]:
        """
        Удаляет категорию и возвращает DTO удалённой категории.

        Args:
            category_id (int): Идентификатор категории.

        Returns:
            Optional[CategoryDTO]: DTO удалённой категории, либо None.
        """
        category = await self._category_repository.get_category_by_id(category_id)
        if not category:
            logger.warning(
                f"Попытка удалить несуществующую категорию (ID={category_id})"
            )
            raise CategoryNotFoundError()

        await self._category_repository.delete_category(category_id)
        logger.info(f"Категория '{category.name}' (ID={category.id}) успешно удалена")

        return CategoryDTO.from_model(category)
