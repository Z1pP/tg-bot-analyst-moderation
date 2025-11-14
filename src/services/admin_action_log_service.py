import logging

from constants.enums import AdminActionType
from repositories import AdminActionLogRepository, UserRepository

logger = logging.getLogger(__name__)


class AdminActionLogService:
    """Сервис для логирования действий администраторов."""

    def __init__(
        self,
        log_repository: AdminActionLogRepository,
        user_repository: UserRepository,
    ):
        self._log_repository = log_repository
        self._user_repository = user_repository

    async def log_action(
        self, admin_tg_id: str, action_type: AdminActionType, details: str = None
    ) -> None:
        """
        Логирует действие администратора.

        Args:
            admin_tg_id: Telegram ID администратора
            action_type: Тип действия
            details: Дополнительная информация о действии (пользователь, чат, период и т.д.)
        """
        try:
            # Получаем пользователя по tg_id
            user = await self._user_repository.get_user_by_tg_id(tg_id=admin_tg_id)
            if not user:
                logger.warning(
                    "Пользователь с tg_id=%s не найден, логирование пропущено",
                    admin_tg_id,
                )
                return

            # Создаем запись в логе
            await self._log_repository.create_log(
                admin_id=user.id, action_type=action_type, details=details
            )
            logger.debug(
                "Записано действие: admin_tg_id=%s, action_type=%s, details=%s",
                admin_tg_id,
                action_type.value,
                details,
            )
        except Exception as e:
            # Не прерываем выполнение основного кода при ошибке логирования
            logger.error("Ошибка при логировании действия: %s", e, exc_info=True)
