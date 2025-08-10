from repositories.user_repository import UserRepository


class DeleteUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, user_id: int) -> bool:
        return await self.user_repository.delete_user(user_id=user_id)
