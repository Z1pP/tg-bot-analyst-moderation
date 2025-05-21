from dto.user import UserDTO
from repositories import UserRepository


class GetAllUsersUseCase:
    def __init__(self, user_repository: UserRepository):
        self._user_repository = user_repository

    async def execute(self, admin_username: str) -> list[UserDTO]:
        users = await self._user_repository.get_all_users(
            exclude=[
                admin_username,
            ]
        )

        return [UserDTO.from_entity(user) for user in users]
