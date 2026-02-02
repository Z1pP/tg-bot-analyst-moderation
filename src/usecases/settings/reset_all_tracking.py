import logging

from repositories import ChatTrackingRepository, UserTrackingRepository
from services import UserService

logger = logging.getLogger(__name__)


class ResetAllTrackingUseCase:
    """Узекейс для сброса всех настроек отслеживания администратора."""

    def __init__(
        self,
        user_service: UserService,
        user_tracking_repository: UserTrackingRepository,
        chat_tracking_repository: ChatTrackingRepository,
    ):
        self._user_service = user_service
        self._user_tracking_repository = user_tracking_repository
        self._chat_tracking_repository = chat_tracking_repository

    async def execute(self, admin_tgid: str) -> None:
        """
        Удаляет всех отслеживаемых пользователей и все отслеживаемые чаты для администратора.

        Args:
            admin_tgid: Telegram ID администратора
        """
        try:
            # Получаем пользователя
            admin = await self._user_service.get_user(tg_id=admin_tgid)
            if not admin:
                logger.error(f"Администратор с tg_id={admin_tgid} не найден")
                return

            # Удаляем всех отслеживаемых пользователей
            deleted_users_count = (
                await self._user_tracking_repository.delete_all_tracked_users_for_admin(
                    admin_id=admin.id
                )
            )

            # Удаляем все отслеживаемые чаты
            deleted_chats_count = (
                await self._chat_tracking_repository.delete_all_tracked_chats_for_admin(
                    admin_id=admin.id
                )
            )

            logger.info(
                "Сброшены настройки для администратора %s (id=%s): "
                "удалено %d пользователей и %d чатов",
                admin_tgid,
                admin.id,
                deleted_users_count,
                deleted_chats_count,
            )

        except Exception as e:
            logger.error(f"Ошибка при сбросе настроек отслеживания: {e}")
            raise
