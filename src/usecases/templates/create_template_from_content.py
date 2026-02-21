"""Use case: создание шаблона из извлечённого контента."""

import logging
from typing import Optional

from dto.template_dto import CreateTemplateFromContentDTO
from models import MessageTemplate
from services.templates import TemplateContentService

logger = logging.getLogger(__name__)


class CreateTemplateFromContentUseCase:
    """Создаёт шаблон из переданного контента (после extract_media_content)."""

    def __init__(self, content_service: TemplateContentService) -> None:
        self._content_service = content_service

    async def execute(
        self, dto: CreateTemplateFromContentDTO
    ) -> Optional[MessageTemplate]:
        """
        Сохраняет шаблон в БД.

        Args:
            dto: author_username и content (словарь с title, text, category_id, chat_id, media_*).

        Returns:
            Созданный MessageTemplate или None при ошибке.
        """
        author = dto.author_username or ""
        return await self._content_service.save_template(
            author_username=author,
            content=dto.content,
        )
