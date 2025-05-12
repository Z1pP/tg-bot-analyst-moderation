from models import ChatSession
from repositories import ChatRepository


class GetOrCreateChatUseCase:
    def __init__(self, chat_repository: ChatRepository):
        self.chat_repository = chat_repository

    async def execute(self, chat_id: str, title: str) -> ChatSession:
        chat = await self.chat_repository.get_chat(chat_id=chat_id)

        if not chat:
            chat = await self.chat_repository.create_chat(chat_id=chat_id, title=title)

        return chat
