from repositories import UserTrackingRepository


class RemoveUserFromTrackingUseCase:
    def __init__(self, user_tracking_repository: UserTrackingRepository):
        self.user_tracking_repository = user_tracking_repository

    async def execute(self, admin_username: str, user_username: str) -> bool:
        """Удаляет пользователя из списка отслеживания админа."""
        return await self.user_tracking_repository.remove_user_from_tracking(
            admin_username=admin_username, user_username=user_username
        )
