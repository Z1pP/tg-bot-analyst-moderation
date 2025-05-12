from dto.message import MessageDTO
from models import ChatSession, User
from repositories.chat_repository import ChatRepository
from repositories.message_repository import MessageRepository
from repositories.user_repository import UserRepository


class SaveMessageUseCase:
    def __init__(
        self,
        user_service: UserRepository,
        message_service: MessageRepository,
        chat_service: ChatRepository,
    ):
        self.user_service = user_service
        self.message_service = message_service
        self.chat_service = chat_service

    async def execute(self, message_dto: MessageDTO):
        # Получаем или создаем юзера
        user = await self._get_or_create_user(
            tg_id=message_dto.user.tg_id, username=message_dto.user.username
        )

        # Получаем или создаем чат
        chat = await self._get_or_create_chat(
            chat_id=message_dto.chat.chat_id, title=message_dto.chat.title
        )

        # Создаем и возвращаем новое сообщение
        return await self.message_service.create_new_message(
            user_id=user.id,
            chat_id=chat.id,
            message_id=message_dto.message_id,
            message_type=message_dto.message_type,
            text=message_dto.text,
        )

    async def _get_or_create_user(self, tg_id: str, username: str) -> User:
        user = await self.user_service.get_user_by_tg_id(tg_id=tg_id)

        if not user:
            user = await self.user_service.create_user(tg_id=tg_id, username=username)

        return user

    async def _get_or_create_chat(self, chat_id: str, title: str) -> ChatSession:
        chat = await self.chat_service.get_chat(chat_id=chat_id)

        if chat:
            chat = await self.chat_service.create_chat(chat_id=chat_id, title=title)

        return chat
