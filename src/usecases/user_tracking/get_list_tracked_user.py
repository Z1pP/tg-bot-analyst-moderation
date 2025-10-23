from models import User
from repositories import UserTrackingRepository


class GetListTrackedUsersUseCase:
    def __init__(self, user_tracking_repository: UserTrackingRepository):
        self._user_tracking_repository = user_tracking_repository

    async def execute(self, admin_tgid: str) -> list[User]:
        return await self._user_tracking_repository.get_tracked_users_by_admin(
            admin_tgid=admin_tgid
        )
