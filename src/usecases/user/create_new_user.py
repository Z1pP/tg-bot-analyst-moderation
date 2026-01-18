from services import UserService


class CreateNewUserUserCase:
    def __init__(self, user_service: UserService):
        self._user_service = user_service

    async def execute(self, tg_id: str = None, username: str = None):
        return await self._user_service.create_user(tg_id=tg_id, username=username)
