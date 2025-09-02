import logging

from dto import CategoryDTO, CreateCategoryDTO
from repositories import TemplateCategoryRepository

logger = logging.getLogger(__name__)


class CreateCategoryUseCase:
    def __init__(self, category_repository: TemplateCategoryRepository):
        self.category_repository = category_repository

    async def execute(self, create_dto: CreateCategoryDTO) -> CategoryDTO:
        """
        Создает новую категорию шаблонов.

        Args:
            name: Название категории

        Returns:
            CategoryDTO: Созданная категория
        """
        try:
            # Валидация названия
            validated_name = self._validate_category_name(create_dto.name)

            # Создание категории
            category = await self.category_repository.create_category(
                name=validated_name
            )

            logger.info(f"Создана новая категория: '{category.name}'")
            return CategoryDTO.from_model(category)

        except Exception as e:
            logger.error(f"Ошибка при создании категории: {e}")
            raise

    def _validate_category_name(self, name: str) -> str:
        """Валидация названия категории"""
        if len(name) > 50:
            raise ValueError("Название категории не может быть длиннее 50 символов")
        if len(name) < 3:
            raise ValueError("Название категории не может быть короче 3 символов")

        return name.strip().upper()
