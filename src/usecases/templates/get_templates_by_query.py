import logging

from dto import TemplateDTO, TemplateSearchResultDTO
from repositories import MessageTemplateRepository

logger = logging.getLogger(__name__)


class GetTemplatesByQueryUseCase:
    def __init__(self, template_repository: MessageTemplateRepository):
        self.template_repository = template_repository

    async def execute(self, query: str) -> TemplateSearchResultDTO:
        """
        Получает шаблоны по поисковому запросу.

        Args:
            query: Поисковый запрос

        Returns:
            TemplateSearchResultDTO: Результат поиска шаблонов
        """
        try:
            templates = await self.template_repository.get_templates_by_query(
                query=query
            )

            # Сортируем по количеству использований от большего к меньшему
            sorted_templates = sorted(templates, key=lambda x: -x.usage_count)

            # Преобразуем в DTO
            template_dtos = [
                TemplateDTO.from_model(template) for template in sorted_templates
            ]

            logger.debug(f"Найдено {len(template_dtos)} шаблонов по запросу '{query}'")

            return TemplateSearchResultDTO(
                templates=template_dtos, total_count=len(template_dtos)
            )

        except Exception as e:
            logger.error(f"Ошибка при поиске шаблонов по запросу '{query}': {e}")
            raise
