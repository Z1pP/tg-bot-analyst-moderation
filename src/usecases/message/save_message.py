from dto.buffer import BufferedMessageDTO
from dto.message import CreateMessageDTO, ResultMessageDTO
from services.analytics_buffer_service import AnalyticsBufferService


class SaveMessageUseCase:
    def __init__(self, buffer_service: AnalyticsBufferService):
        self.buffer_service = buffer_service

    async def execute(self, message_dto: CreateMessageDTO) -> ResultMessageDTO:
        """
        Сохраняет сообщение в буфер Redis для последующей батч-обработки.

        Возвращает "заглушку" ResultMessageDTO, так как сообщение еще не сохранено в БД.
        ID будет присвоен после обработки воркером.
        """
        # Конвертируем CreateMessageDTO в BufferedMessageDTO
        buffered_dto = BufferedMessageDTO(
            chat_id=message_dto.chat_id,
            user_id=message_dto.user_id,
            message_id=message_dto.message_id,
            message_type=message_dto.message_type,
            content_type=message_dto.content_type,
            text=message_dto.text,
            created_at=message_dto.created_at,
        )

        # Добавляем в буфер Redis
        await self.buffer_service.add_message(buffered_dto)

        # Возвращаем заглушку (ID будет присвоен после обработки воркером)
        return ResultMessageDTO(
            id=0,  # Временное значение, будет обновлено после сохранения в БД
            db_chat_id=message_dto.chat_id,
            db_user_id=message_dto.user_id,
            message_id=message_dto.message_id,
            message_type=message_dto.message_type,
            content_type=message_dto.content_type,
            text=message_dto.text,
            created_at=message_dto.created_at,
        )
