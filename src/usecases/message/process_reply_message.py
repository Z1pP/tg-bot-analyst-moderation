from dto.message_reply import CreateMessageReplyDTO
from repositories.message_repository import MessageRepository


class ProcessReplyMessageUseCase:
    def __init__(self, message_repository: MessageRepository):
        self.message_repository = message_repository

    async def execute(self, reply_message_dto: CreateMessageReplyDTO):
        """
        Сохраняет связь между reply-сообщением и оригинальным сообщением.
        """
        await self.message_repository.create_reply_message(dto=reply_message_dto)
