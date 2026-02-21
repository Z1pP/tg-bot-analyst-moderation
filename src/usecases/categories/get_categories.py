"""Use case: получение списка всех категорий."""

from typing import List

from models import TemplateCategory
from services import CategoryService


class GetCategoriesUseCase:
    """Возвращает список всех категорий шаблонов (с кешем)."""

    def __init__(self, category_service: CategoryService) -> None:
        self._category_service = category_service

    async def execute(self) -> List[TemplateCategory]:
        result = await self._category_service.get_categories()
        return list(result)
