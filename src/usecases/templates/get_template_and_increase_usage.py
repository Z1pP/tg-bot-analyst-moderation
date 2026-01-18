import logging
from typing import Optional

from models import MessageTemplate
from services.templates.template_service import TemplateService

logger = logging.getLogger(__name__)


class GetTemplateAndIncreaseUsageUseCase:
    def __init__(self, template_service: TemplateService):
        self._template_service = template_service

    async def execute(
        self, template_id: int, chat_id: str
    ) -> Optional[MessageTemplate]:
        """
        Получает шаблон и увеличивает счетчик использования.

        Args:
            template_id: ID шаблона
            chat_id: ID чата

        Returns:
            Optional[MessageTemplate]: Шаблон или None
        """
        try:
            template = await self._template_service.get_template_and_increase_usage(
                template_id=template_id, chat_id=chat_id
            )

            if template:
                logger.debug(
                    f"Получен шаблон {template_id}, использований: {template.usage_count}"
                )
            else:
                logger.warning(f"Шаблон {template_id} не найден")

            return template

        except Exception as e:
            logger.error(f"Ошибка при получении шаблона {template_id}: {e}")
            raise
