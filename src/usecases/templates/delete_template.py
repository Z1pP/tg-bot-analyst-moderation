import logging
from typing import Optional

from constants.enums import AdminActionType
from services.admin_action_log_service import AdminActionLogService
from services.templates.template_service import TemplateService

logger = logging.getLogger(__name__)


class DeleteTemplateUseCase:
    def __init__(
        self,
        template_service: TemplateService,
        admin_action_log_service: AdminActionLogService,
    ) -> None:
        self._template_service = template_service
        self._admin_action_log_service = admin_action_log_service

    async def execute(
        self, template_id: int, admin_tg_id: Optional[str] = None
    ) -> bool:
        """
        Удаляет шаблон.

        Args:
            template_id: ID шаблона
            admin_tg_id: Telegram ID администратора (опционально)

        Returns:
            bool: True если удаление успешно
        """
        result = await self._template_service.delete_template(
            template_id=template_id
        )
        if not result:
            return False

        logger.info("Шаблон с ID=%s успешно удален", template_id)

        # Логируем действие после успешного удаления шаблона
        if self._admin_action_log_service and admin_tg_id:
            await self._admin_action_log_service.log_action(
                admin_tg_id=admin_tg_id,
                action_type=AdminActionType.DELETE_TEMPLATE,
            )

        return True
