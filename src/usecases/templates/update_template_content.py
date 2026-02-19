"""Use case: обновление контента шаблона."""

import logging
from typing import Any, Dict

from services.templates import TemplateContentService

logger = logging.getLogger(__name__)


class UpdateTemplateContentUseCase:
    """Обновляет содержимое шаблона (текст и медиа) по переданному словарю контента."""

    def __init__(self, content_service: TemplateContentService) -> None:
        self._content_service = content_service

    async def execute(self, template_id: int, content: Dict[str, Any]) -> bool:
        """
        Обновляет контент шаблона.

        Args:
            template_id: ID шаблона.
            content: Словарь с text, media_types, media_files, media_unique_ids и т.д.

        Returns:
            True при успехе, False при ошибке.
        """
        return await self._content_service.update_template_content(
            template_id=template_id,
            content=content,
        )
