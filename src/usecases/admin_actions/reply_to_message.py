import logging

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from dto.message_action import MessageActionDTO
from exceptions.moderation import MessageSendError
from services import BotMessageService, ChatService

logger = logging.getLogger(__name__)


class ReplyToMessageUseCase:
    """UseCase для ответа на сообщение от имени бота."""

    def __init__(
        self,
        bot_message_service: BotMessageService,
        chat_service: ChatService,
    ):
        self.bot_message_service = bot_message_service
        self.chat_service = chat_service

    async def execute(self, dto: MessageActionDTO) -> None:
        """Отправляет ответ на сообщение от имени бота (копирует контент)."""
        logger.info(
            "Ответ на сообщение %s в чате %s админом %s",
            dto.message_id,
            dto.chat_tgid,
            dto.admin_tgid,
        )

        if not dto.admin_message_id:
            logger.error("Отсутствует admin_message_id для копирования")
            raise MessageSendError("Отсутствует сообщение для копирования")

        try:
            is_sent = await self.bot_message_service.copy_message_as_reply(
                chat_tgid=dto.chat_tgid,
                from_chat_tgid=dto.admin_tgid,
                message_id=dto.admin_message_id,
                reply_to_message_id=dto.message_id,
            )
            if not is_sent:
                raise MessageSendError("Не удалось скопировать сообщение")
            logger.info("Ответ на сообщение %s отправлен", dto.message_id)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.error(
                "Ошибка отправки ответа на сообщение %s: %s",
                dto.message_id,
                e,
                exc_info=True,
            )
            raise MessageSendError(str(e))

        try:
            archive_chats = await self.chat_service.get_archive_chats(
                source_chat_tgid=dto.chat_tgid,
            )
            if archive_chats:
                chat = await self.chat_service.get_chat(chat_id=dto.chat_tgid)
                report_text = (
                    f"💬 <b>Ответ от бота</b>\n\n"
                    f"• ID сообщения: {dto.message_id}\n"
                    f"• Чат: {chat.title}\n"
                    f"• Отправил: @{dto.admin_username}"
                )

                for archive_chat in archive_chats:
                    try:
                        await self.bot_message_service.send_chat_message(
                            chat_tgid=archive_chat.chat_id,
                            text=report_text,
                        )
                    except (TelegramBadRequest, TelegramForbiddenError) as e:
                        logger.warning(
                            "Не удалось отправить отчет в архивный чат %s: %s",
                            archive_chat.chat_id,
                            e,
                        )
        except Exception as e:
            logger.debug("Архивные чаты не найдены или ошибка: %s", e)
