from services import UserService


class DeleteUserUseCase:
    def __init__(self, user_service: UserService) -> None:
        self._user_service = user_service

    async def execute(self, user_id: int) -> bool:
        result: bool = await self._user_service.delete_user(user_id=user_id)
        return result
