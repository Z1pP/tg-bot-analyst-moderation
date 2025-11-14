import logging

from constants.enums import AdminActionType
from dto import CategoryDTO, CreateCategoryDTO
from exceptions.category import CategoryAlreadyExists
from repositories import TemplateCategoryRepository
from services import AdminActionLogService

logger = logging.getLogger(__name__)


class CreateCategoryUseCase:
    def __init__(
        self,
        category_repository: TemplateCategoryRepository,
        admin_action_log_service: AdminActionLogService = None,
    ):
        self.category_repository = category_repository
        self._admin_action_log_service = admin_action_log_service

    async def execute(
        self, dto: CreateCategoryDTO, admin_tg_id: str = None
    ) -> CategoryDTO:
        """
        Создает новую категорию шаблонов.

        Args:
            dto: DTO с названием категории
            admin_tg_id: Telegram ID администратора (опционально)

        Returns:
            CategoryDTO: Созданная категория
        """
        existing = await self.category_repository.get_category_by_name(name=dto.name)

        if existing:
            logger.warning(f"Категория с именем '{dto.name}' уже существует")
            raise CategoryAlreadyExists(name=dto.name)

        category = await self.category_repository.create_category(name=dto.name)

        logger.info(f"Создана новая категория: '{category.name}'")

        # Логируем действие после успешного создания категории
        if self._admin_action_log_service and admin_tg_id:
            await self._admin_action_log_service.log_action(
                admin_tg_id=admin_tg_id,
                action_type=AdminActionType.ADD_CATEGORY,
            )

        return CategoryDTO.from_model(category)
