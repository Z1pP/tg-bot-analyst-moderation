import logging

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from dto.message_action import MessageActionDTO
from exceptions.moderation import MessageDeleteError, MessageSendError
from services import BotMessageService, ChatService

logger = logging.getLogger(__name__)


class DeleteMessageUseCase:
    """UseCase для удаления сообщения из чата."""

    def __init__(
        self,
        bot_message_service: BotMessageService,
        chat_service: ChatService,
    ):
        self.bot_message_service = bot_message_service
        self.chat_service = chat_service

    async def execute(self, dto: MessageActionDTO) -> None:
        """Удаляет сообщение из чата."""
        logger.info(
            "Удаление сообщения %s из чата %s админом %s",
            dto.message_id,
            dto.chat_tgid,
            dto.admin_tgid,
        )

        try:
            is_deleted = await self.bot_message_service.delete_message_from_chat(
                chat_id=dto.chat_tgid,
                message_id=dto.message_id,
            )
            if not is_deleted:
                logger.warning(
                    "Сообщение %s не удалено (возможно старше 48ч)",
                    dto.message_id,
                )
                raise MessageDeleteError()
            logger.info("Сообщение %s успешно удалено", dto.message_id)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.error(
                "Ошибка удаления сообщения %s: %s",
                dto.message_id,
                e,
                exc_info=True,
            )
            raise MessageSendError(str(e))
