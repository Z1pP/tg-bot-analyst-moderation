from dto.message_reply import CreateMessageReplyDTO
from repositories.message_reply_repository import MessageReplyRepository
from services.work_time_service import WorkTimeService


class SaveModeratorReplyMessageUseCase:
    def __init__(self, msg_reply_repository: MessageReplyRepository):
        self._msg_reply_repository = msg_reply_repository

    async def execute(self, reply_message_dto: CreateMessageReplyDTO):
        """
        Сохраняет связь между reply-сообщением и оригинальным сообщением,
        если сообщения созданы в один день и в рабочее время.
        """
        if self._should_save_reply(reply_message_dto):
            await self._msg_reply_repository.create_reply_message(dto=reply_message_dto)

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
