import logging

from dto import CategoryDTO, CreateCategoryDTO
from exceptions.category import CategoryAlreadyExists
from repositories import TemplateCategoryRepository

logger = logging.getLogger(__name__)


class CreateCategoryUseCase:
    def __init__(self, category_repository: TemplateCategoryRepository):
        self.category_repository = category_repository

    async def execute(self, dto: CreateCategoryDTO) -> CategoryDTO:
        """
        Создает новую категорию шаблонов.

        Args:
            name: Название категории

        Returns:
            CategoryDTO: Созданная категория
        """
        existing = await self.category_repository.get_category_by_name(name=dto.name)

        if existing:
            logger.warning(f"Категория с именем '{dto.name}' уже существует")
            raise CategoryAlreadyExists(name=dto.name)

        category = await self.category_repository.create_category(name=dto.name)

        logger.info(f"Создана новая категория: '{category.name}'")
        return CategoryDTO.from_model(category)
