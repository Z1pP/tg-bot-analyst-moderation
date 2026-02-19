"""Use case: получение шаблона по ID."""

import logging
from typing import Optional

from models import MessageTemplate
from services.templates import TemplateService

logger = logging.getLogger(__name__)


class GetTemplateByIdUseCase:
    """Возвращает шаблон по идентификатору или None."""

    def __init__(self, template_service: TemplateService) -> None:
        self._template_service = template_service

    async def execute(self, template_id: int) -> Optional[MessageTemplate]:
        """Получает шаблон по ID."""
        return await self._template_service.get_template_by_id(
            template_id=template_id
        )
