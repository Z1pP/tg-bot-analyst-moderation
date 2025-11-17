import logging

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from constants.enums import AdminActionType
from dto.message_action import SendMessageDTO
from exceptions.moderation import MessageSendError
from services import AdminActionLogService, BotMessageService, ChatService

logger = logging.getLogger(__name__)


class SendMessageToChatUseCase:
    """UseCase для отправки сообщения в чат от имени бота."""

    def __init__(
        self,
        bot_message_service: BotMessageService,
        chat_service: ChatService,
        admin_action_log_service: AdminActionLogService = None,
    ):
        self.bot_message_service = bot_message_service
        self.chat_service = chat_service
        self._admin_action_log_service = admin_action_log_service

    async def execute(self, dto: SendMessageDTO) -> None:
        """Отправляет сообщение в чат от имени бота (копирует контент)."""
        logger.info(
            "Отправка сообщения в чат %s админом %s",
            dto.chat_tgid,
            dto.admin_tgid,
        )

        try:
            sent_message_id = await self.bot_message_service.copy_message(
                chat_tgid=dto.chat_tgid,
                from_chat_tgid=dto.admin_tgid,
                message_id=dto.admin_message_id,
            )
            if not sent_message_id:
                raise MessageSendError("Не удалось скопировать сообщение")
            logger.info("Сообщение отправлено в чат %s", dto.chat_tgid)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.error(
                "Ошибка отправки сообщения в чат %s: %s",
                dto.chat_tgid,
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

                chat_id_str = str(dto.chat_tgid).replace("-100", "")
                message_link = f"https://t.me/c/{chat_id_str}/{sent_message_id}"

                report_text = (
                    f"💬 <b>Сообщение от бота</b>\n\n"
                    f"Чат: {chat.title}\n"
                    f"Отправил: @{dto.admin_username}\n"
                    f"<a href='{message_link}'>Ссылка на сообщение</a>"
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

        # Логируем действие после успешной отправки сообщения
        if self._admin_action_log_service:
            await self._admin_action_log_service.log_action(
                admin_tg_id=dto.admin_tgid,
                action_type=AdminActionType.SEND_MESSAGE,
            )
