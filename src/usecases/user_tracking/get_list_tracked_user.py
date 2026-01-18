from dto.user import UserDTO
from repositories import UserTrackingRepository


class GetListTrackedUsersUseCase:
    def __init__(self, user_tracking_repository: UserTrackingRepository):
        self._user_tracking_repository = user_tracking_repository

    async def execute(self, admin_tgid: str) -> list[UserDTO]:
        users_with_dates = (
            await self._user_tracking_repository.get_tracked_users_with_dates(
                admin_tgid=admin_tgid
            )
        )
        return [
            UserDTO.from_model(user, added_at=added_at)
            for user, added_at in users_with_dates
        ]
