from dto.buffer import BufferedMessageDTO
from dto.message import CreateMessageDTO
from services.analytics_buffer_service import AnalyticsBufferService
from services.chat.chat_service import ChatService
from services.user.user_service import UserService


class SaveMessageUseCase:
    def __init__(
        self,
        buffer_service: AnalyticsBufferService,
        user_service: UserService,
        chat_service: ChatService,
    ):
        self.buffer_service = buffer_service
        self.user_service = user_service
        self.chat_service = chat_service

    async def execute(self, message_dto: CreateMessageDTO) -> None:
        """
        Сохраняет сообщение в буфер Redis для последующей батч-обработки.

        Возвращает "заглушку" ResultMessageDTO, так как сообщение еще не сохранено в БД.
        ID будет присвоен после обработки воркером.
        """

        user = await self.user_service.get_or_create(
            tg_id=message_dto.user_tgid,
            username=message_dto.user_username,
        )
        chat = await self.chat_service.get_or_create(
            chat_tgid=message_dto.chat_tgid,
        )

        # Конвертируем CreateMessageDTO в BufferedMessageDTO
        buffered_dto = BufferedMessageDTO(
            chat_id=chat.id,
            user_id=user.id,
            message_id=message_dto.message_id,
            message_type=message_dto.message_type,
            content_type=message_dto.content_type,
            text=message_dto.text,
            created_at=message_dto.created_at,
        )

        # Добавляем в буфер Redis
        await self.buffer_service.add_message(buffered_dto)
