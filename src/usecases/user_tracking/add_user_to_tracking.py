from repositories import UserRepository, UserTrackingRepository


class AddUserToTrackingUseCase:
    def __init__(
        self,
        user_tracking_repository: UserTrackingRepository,
        user_repository: UserRepository,
    ):
        self._user_tracking_repository = user_tracking_repository
        self._user_repository = user_repository

    async def execute(self, admin_username: str, user_username: str) -> bool:
        user = await self._user_repository.get_user_by_username(username=user_username)
        if not user:
            user = await self._user_repository.create_user(username=user_username)

        return await self._user_tracking_repository.add_user_to_tracking(
            admin_username=admin_username,
            user_username=user_username,
        )
