import logging

from repositories import MessageTemplateRepository

logger = logging.getLogger(__name__)


class UpdateTemplateTitleUseCase:
    def __init__(self, template_repository: MessageTemplateRepository):
        self.template_repository = template_repository

    async def execute(self, template_id: int, new_title: str) -> bool:
        """
        Обновляет название шаблона.

        Args:
            template_id: ID шаблона
            new_title: Новое название

        Returns:
            bool: True если обновление успешно
        """
        try:
            success = await self.template_repository.update_template_title(
                template_id, new_title
            )

            if success:
                logger.info(f"Название шаблона {template_id} изменено на '{new_title}'")
            else:
                logger.warning(f"Не удалось обновить название шаблона {template_id}")

            return success

        except Exception as e:
            logger.error(f"Ошибка при обновлении названия шаблона: {e}")
            raise
