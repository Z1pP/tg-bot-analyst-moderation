from dto.chat_dto import ChatReadDTO
from repositories import ChatRepository


class GetAllChatsUseCase:
    def __init__(self, chat_repository: ChatRepository):
        self._chat_repository = chat_repository

    async def execute(self):
        chats = await self._chat_repository.get_all()

        return [ChatReadDTO.from_entity(chat) for chat in chats]
