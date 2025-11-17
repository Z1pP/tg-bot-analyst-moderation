import logging

from constants.enums import AdminActionType
from repositories import MessageTemplateRepository
from services import AdminActionLogService

logger = logging.getLogger(__name__)


class DeleteTemplateUseCase:
    def __init__(
        self,
        template_repository: MessageTemplateRepository,
        admin_action_log_service: AdminActionLogService = None,
    ):
        self.template_repository = template_repository
        self._admin_action_log_service = admin_action_log_service

    async def execute(self, template_id: int, admin_tg_id: str = None) -> bool:
        """
        Удаляет шаблон.

        Args:
            template_id: ID шаблона
            admin_tg_id: Telegram ID администратора (опционально)

        Returns:
            bool: True если удаление успешно
        """
        try:
            await self.template_repository.delete_template(template_id=template_id)
            logger.info(f"Шаблон с ID={template_id} успешно удален")

            # Логируем действие после успешного удаления шаблона
            if self._admin_action_log_service and admin_tg_id:
                await self._admin_action_log_service.log_action(
                    admin_tg_id=admin_tg_id,
                    action_type=AdminActionType.DELETE_TEMPLATE,
                )

            return True

        except Exception as e:
            logger.error(f"Ошибка при удалении шаблона {template_id}: {e}")
            raise
