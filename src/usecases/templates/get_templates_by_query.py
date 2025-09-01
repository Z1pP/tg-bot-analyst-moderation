import logging
from typing import List

from models import MessageTemplate
from repositories import MessageTemplateRepository

logger = logging.getLogger(__name__)


class GetTemplatesByQueryUseCase:
    def __init__(self, template_repository: MessageTemplateRepository):
        self.template_repository = template_repository

    async def execute(self, query: str) -> List[MessageTemplate]:
        """
        Получает шаблоны по поисковому запросу.

        Args:
            query: Поисковый запрос

        Returns:
            List[MessageTemplate]: Список шаблонов, отсортированный по использованию
        """
        try:
            templates = await self.template_repository.get_templates_by_query(
                query=query
            )

            # Сортируем по количеству использований от большего к меньшему
            sorted_templates = sorted(templates, key=lambda x: -x.usage_count)

            logger.debug(
                f"Найдено {len(sorted_templates)} шаблонов по запросу '{query}'"
            )
            return sorted_templates

        except Exception as e:
            logger.error(f"Ошибка при поиске шаблонов по запросу '{query}': {e}")
            raise
