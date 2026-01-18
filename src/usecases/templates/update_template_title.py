import logging

from dto import UpdateTemplateTitleDTO
from services.templates.template_service import TemplateService

logger = logging.getLogger(__name__)


class UpdateTemplateTitleUseCase:
    def __init__(self, template_service: TemplateService):
        self._template_service = template_service

    async def execute(self, update_dto: UpdateTemplateTitleDTO) -> bool:
        """
        Обновляет название шаблона.

        Args:
            update_dto: Данные для обновления

        Returns:
            bool: True если обновление успешно
        """
        try:
            success = await self._template_service.update_template_title(
                update_dto.template_id, update_dto.new_title
            )

            if success:
                logger.info(
                    f"Название шаблона {update_dto.template_id} изменено на '{update_dto.new_title}'"
                )
            else:
                logger.warning(
                    f"Не удалось обновить название шаблона {update_dto.template_id}"
                )

            return success

        except Exception as e:
            logger.error(f"Ошибка при обновлении названия шаблона: {e}")
            raise
