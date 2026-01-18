import logging

from constants.enums import AdminActionType
from dto import CategoryDTO, CreateCategoryDTO
from exceptions.category import CategoryAlreadyExists
from services import AdminActionLogService, CategoryService

logger = logging.getLogger(__name__)


class CreateCategoryUseCase:
    def __init__(
        self,
        category_service: CategoryService,
        admin_action_log_service: AdminActionLogService = None,
    ):
        self._category_service = category_service
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
        categories = await self._category_service.get_categories()
        existing = next((c for c in categories if c.name == dto.name), None)

        if existing:
            logger.warning(f"Категория с именем '{dto.name}' уже существует")
            raise CategoryAlreadyExists(name=dto.name)

        category = await self._category_service.create_category(name=dto.name)

        logger.info(f"Создана новая категория: '{category.name}'")

        # Логируем действие после успешного создания категории
        if self._admin_action_log_service and admin_tg_id:
            await self._admin_action_log_service.log_action(
                admin_tg_id=admin_tg_id,
                action_type=AdminActionType.ADD_CATEGORY,
            )

        return CategoryDTO.from_model(category)
