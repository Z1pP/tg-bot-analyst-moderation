from dto import RemoveUserTrackingDTO
from repositories import UserTrackingRepository
from services import UserService


class RemoveUserFromTrackingUseCase:
    def __init__(
        self,
        user_tracking_repository: UserTrackingRepository,
        user_service: UserService,
    ):
        self.user_tracking_repository = user_tracking_repository
        self.user_service = user_service

    async def execute(self, dto: RemoveUserTrackingDTO) -> bool:
        """Удаляет пользователя из списка отслеживания админа."""
        admin = await self.user_service.get_user(
            tg_id=dto.admin_tgid,
            username=dto.admin_username,
        )

        if not admin:
            return False

        await self.user_tracking_repository.remove_user_from_tracking(
            admin_id=admin.id,
            user_id=dto.user_id,
        )
        return True
