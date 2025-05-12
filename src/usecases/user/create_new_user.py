from repositories import UserRepository


class CreateNewUserUserCase:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def execute(self, tg_id: str = None, username: str = None):
        return await self.user_repository.create_user(tg_id=tg_id, username=username)
