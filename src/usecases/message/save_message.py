from dto.message import CreateMessageDTO, ResultMessageDTO
from repositories.message_repository import MessageRepository


class SaveMessageUseCase:
    def __init__(self, message_repository: MessageRepository):
        self.message_repository = message_repository

    async def execute(self, message_dto: CreateMessageDTO) -> ResultMessageDTO:
        # Создаем и возвращаем новое сообщение
        message_db = await self.message_repository.create_new_message(dto=message_dto)

        return ResultMessageDTO.from_model(message_db)
