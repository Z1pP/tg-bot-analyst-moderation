from dto.message_reply import CreateMessageReplyDTO
from repositories.message_reply_repository import MessageReplyRepository


class ProcessReplyMessageUseCase:
    def __init__(self, msg_reply_repository: MessageReplyRepository):
        self._msg_reply_repository = msg_reply_repository

    async def execute(self, reply_message_dto: CreateMessageReplyDTO):
        """
        Сохраняет связь между reply-сообщением и оригинальным сообщением.
        """
        await self._msg_reply_repository.create_reply_message(dto=reply_message_dto)
