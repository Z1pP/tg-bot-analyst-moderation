from dto.message import CreateMessageDTO
from dto.message_reply import CreateMessageReplyDTO, ResultMessageReplyDTO
from repositories.message_repository import MessageRepository


class SaveReplyMessageUseCase:
    def __init__(self, message_repository: MessageRepository):
        self.message_repository = message_repository

    async def execute(
        self,
        reply_message_dto: CreateMessageReplyDTO,
    ) -> ResultMessageReplyDTO:
        message_db = await self.message_repository.create_new_message(
            dto=CreateMessageDTO.from_reply_dto(reply_message_dto)
        )

        reply_db = await self.message_repository.create_reply_message(
            dto=reply_message_dto, message_id=message_db.id
        )
