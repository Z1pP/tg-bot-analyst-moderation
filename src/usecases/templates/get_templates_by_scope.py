"""Use case: получение шаблонов по области (глобальные или для чата)."""

import logging
from typing import List, Tuple

from dto.template_dto import GetTemplatesByScopeDTO
from exceptions import ValidationException
from models import MessageTemplate
from services.templates import TemplateService

logger = logging.getLogger(__name__)


class GetTemplatesByScopeUseCase:
    """Возвращает список шаблонов по области (global/chat) и общее количество."""

    def __init__(self, template_service: TemplateService) -> None:
        self._template_service = template_service

    async def execute(
        self, dto: GetTemplatesByScopeDTO
    ) -> Tuple[List[MessageTemplate], int]:
        """
        Получает шаблоны: глобальные или для указанного чата.

        Returns:
            (список шаблонов, общее количество)
        """
        if dto.scope == "global":
            templates = await self._template_service.get_global_templates_paginated(
                page=dto.page,
                page_size=dto.page_size,
            )
            total_count = await self._template_service.get_global_templates_count()
        else:
            if dto.chat_id is None:
                raise ValidationException(
                    message="chat_id обязателен для scope=chat"
                )
            templates = await self._template_service.get_chat_templates_paginated(
                chat_id=dto.chat_id,
                page=dto.page,
                page_size=dto.page_size,
            )
            total_count = await self._template_service.get_chat_templates_count(
                chat_id=dto.chat_id
            )
        return templates, total_count
