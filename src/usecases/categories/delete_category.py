import logging

from repositories import TemplateCategoryRepository

logger = logging.getLogger(__name__)


class DeleteCategoryUseCase:
    def __init__(self, category_repository: TemplateCategoryRepository):
        self.category_repository = category_repository

    async def execute(self, category_id: int) -> bool:
        """
        Удаляет категорию.

        Args:
            category_id: ID категории

        Returns:
            bool: True если удаление успешно
        """
        try:
            await self.category_repository.delete_category(category_id=category_id)
            logger.info(f"Категория с ID={category_id} успешно удалена")
            return True

        except Exception as e:
            logger.error(f"Ошибка при удалении категории {category_id}: {e}")
            raise
