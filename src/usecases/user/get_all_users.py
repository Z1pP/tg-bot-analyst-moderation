from dto.user import UserDTO
from repositories import UserRepository


class GetAllUsersUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def execute(self) -> list[UserDTO]:
        users = await self._user_repository.get_all_moderators()

        return [UserDTO.from_model(user) for user in users]
