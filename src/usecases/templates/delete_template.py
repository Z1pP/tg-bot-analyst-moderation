import logging

from repositories import MessageTemplateRepository

logger = logging.getLogger(__name__)


class DeleteTemplateUseCase:
    def __init__(self, template_repository: MessageTemplateRepository):
        self.template_repository = template_repository

    async def execute(self, template_id: int) -> bool:
        """
        Удаляет шаблон.

        Args:
            template_id: ID шаблона

        Returns:
            bool: True если удаление успешно
        """
        try:
            await self.template_repository.delete_template(template_id=template_id)
            logger.info(f"Шаблон с ID={template_id} успешно удален")
            return True

        except Exception as e:
            logger.error(f"Ошибка при удалении шаблона {template_id}: {e}")
            raise
