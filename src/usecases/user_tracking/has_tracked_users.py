from repositories import UserTrackingRepository


class HasTrackedUsersUseCase:
    """Узекейс для проверки наличия отслеживаемых пользователей у админа."""

    def __init__(self, user_tracking_repository: UserTrackingRepository):
        self._user_tracking_repository = user_tracking_repository

    async def execute(self, admin_tgid: str) -> bool:
        """
        Проверяет, есть ли у админа хотя бы один отслеживаемый пользователь.

        Args:
            admin_tgid: Telegram ID администратора

        Returns:
            True, если есть хотя бы один отслеживаемый пользователь, иначе False
        """
        return await self._user_tracking_repository.has_tracked_users(admin_tgid)
