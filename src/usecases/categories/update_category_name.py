import logging

from repositories import TemplateCategoryRepository

logger = logging.getLogger(__name__)


class UpdateCategoryNameUseCase:
    def __init__(self, category_repository: TemplateCategoryRepository):
        self.category_repository = category_repository

    async def execute(self, category_id: int, new_name: str) -> bool:
        """
        Обновляет название категории.

        Args:
            category_id: ID категории
            new_name: Новое название

        Returns:
            bool: True если обновление успешно
        """
        try:
            success = await self.category_repository.update_category_name(
                category_id, new_name
            )

            if success:
                logger.info(
                    f"Название категории {category_id} изменено на '{new_name}'"
                )
            else:
                logger.warning(f"Не удалось обновить название категории {category_id}")

            return success

        except Exception as e:
            logger.error(f"Ошибка при обновлении названия категории: {e}")
            raise
