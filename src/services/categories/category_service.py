from typing import List

from models import TemplateCategory
from repositories import TemplateCategoryRepository


class CategoryService:
    """Сервис для работы с категориями шаблонов"""

    def __init__(self, category_repository: TemplateCategoryRepository):
        self._category_repository = category_repository

    async def get_categories(self) -> List[TemplateCategory]:
        """Получает список шаблонов из БД"""

        return await self._category_repository.get_all_categories()
