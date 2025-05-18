from repositories.user_repository import UserRepository


class DeleteUserUseCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, username: str):
        user = await self.user_repository.get_user_by_username(username=username)

        if user is None:
            raise ValueError(f"User with username {username} not found")
        await self.user_repository.delete_user(user=user)
