import logging
from typing import Optional

from constants.enums import AdminActionType
from dto import CategoryDTO
from exceptions.category import CategoryNotFoundError
from repositories import TemplateCategoryRepository
from services import AdminActionLogService

logger = logging.getLogger(__name__)


class DeleteCategoryUseCase:
    """Use case для удаления категории шаблонов."""

    def __init__(
        self,
        category_repository: TemplateCategoryRepository,
        admin_action_log_service: AdminActionLogService = None,
    ):
        self._category_repository = category_repository
        self._admin_action_log_service = admin_action_log_service

    async def execute(
        self, category_id: int, admin_tg_id: str = None
    ) -> Optional[CategoryDTO]:
        """
        Удаляет категорию и возвращает DTO удалённой категории.

        Args:
            category_id (int): Идентификатор категории.
            admin_tg_id: Telegram ID администратора (опционально)

        Returns:
            Optional[CategoryDTO]: DTO удалённой категории, либо None.
        """
        category = await self._category_repository.get_category_by_id(category_id)
        if not category:
            logger.warning(
                f"Попытка удалить несуществующую категорию (ID={category_id})"
            )
            raise CategoryNotFoundError()

        await self._category_repository.delete_category(category_id)
        logger.info(f"Категория '{category.name}' (ID={category.id}) успешно удалена")

        # Логируем действие после успешного удаления категории
        if self._admin_action_log_service and admin_tg_id:
            await self._admin_action_log_service.log_action(
                admin_tg_id=admin_tg_id,
                action_type=AdminActionType.DELETE_CATEGORY,
            )

        return CategoryDTO.from_model(category)
