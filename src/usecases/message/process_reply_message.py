from dto.buffer import BufferedMessageReplyDTO
from dto.message_reply import CreateMessageReplyDTO
from services import ChatService, UserService
from services.analytics_buffer_service import AnalyticsBufferService
from services.work_time_service import WorkTimeService


class SaveReplyMessageUseCase:
    def __init__(
        self,
        buffer_service: AnalyticsBufferService,
        user_service: UserService,
        chat_service: ChatService,
    ):
        self.buffer_service = buffer_service
        self.user_service = user_service
        self.chat_service = chat_service

    async def execute(self, reply_message_dto: CreateMessageReplyDTO):
        """
        Сохраняет связь между reply-сообщением и оригинальным сообщением в буфер Redis,
        если сообщения созданы в один день и в рабочее время.
        """

        reply_user = await self.user_service.get_or_create(
            tg_id=reply_message_dto.reply_user_tgid,
        )
        chat = await self.chat_service.get_or_create(
            chat_tgid=reply_message_dto.chat_tgid,
        )
        if self._should_save_reply(reply_message_dto):
            # Конвертируем CreateMessageReplyDTO в BufferedMessageReplyDTO
            # Используем reply_message_id_str (Telegram message_id) вместо reply_message_id (DB id)
            # В воркере будем искать ChatMessage по message_id для получения DB id
            buffered_dto = BufferedMessageReplyDTO(
                chat_id=chat.id,
                reply_user_id=reply_user.id,
                original_message_url=reply_message_dto.original_message_url,
                reply_message_id_str=reply_message_dto.reply_message_id_str
                or str(reply_message_dto.reply_message_id),
                response_time_seconds=reply_message_dto.response_time_seconds,
                created_at=reply_message_dto.reply_message_date,
            )

            # Добавляем в буфер Redis
            await self.buffer_service.add_reply(buffered_dto)

    def _should_save_reply(self, dto: CreateMessageReplyDTO) -> bool:
        """
        Проверяет, нужно ли сохранять reply-сообщение.

        Условия:
        1. Оригинальное сообщение и ответ должны быть созданы в один день
        2. Время создания должно входить в рабочее время с учетом допустимого отклонения

        Returns:
            bool: True если сообщение нужно сохранить, False в противном случае
        """
        # Проверяем, что сообщения созданы в один день
        if dto.original_message_date.date() != dto.reply_message_date.date():
            return False

        # Проверяем, что ответ создан в рабочее время
        if not WorkTimeService.is_work_time(
            current_time=dto.reply_message_date.time(),
        ):
            return False

        return True
