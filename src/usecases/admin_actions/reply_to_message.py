import logging

from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
)

from constants.enums import AdminActionType
from dto.message_action import MessageActionDTO
from exceptions import BotBaseException
from exceptions.moderation import MessageSendError
from services import AdminActionLogService, BotMessageService, ChatService
from services.time_service import TimeZoneService

logger = logging.getLogger(__name__)


class ReplyToMessageUseCase:
    """UseCase для ответа на сообщение от имени бота."""

    def __init__(
        self,
        bot_message_service: BotMessageService,
        chat_service: ChatService,
        admin_action_log_service: AdminActionLogService,
    ) -> None:
        self.bot_message_service = bot_message_service
        self.chat_service = chat_service
        self._admin_action_log_service = admin_action_log_service

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
            sent_message_id = await self.bot_message_service.copy_message_as_reply(
                chat_tgid=dto.chat_tgid,
                from_chat_tgid=dto.admin_tgid,
                message_id=dto.admin_message_id,
                reply_to_message_id=dto.message_id,
            )
            if not sent_message_id:
                raise MessageSendError(
                    "❌ Не удалось скопировать сообщение. Возможно, сообщение было удалено или недоступно."
                )
            logger.info("Ответ на сообщение %s отправлен", dto.message_id)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            error_message = str(e)
            if (
                "message to copy not found" in error_message.lower()
                or "message not found" in error_message.lower()
            ):
                user_message = "❌ Сообщение для копирования не найдено. Возможно, оно было удалено или недоступно."
            else:
                user_message = f"❌ Ошибка при отправке ответа: {error_message}"

            logger.error(
                "Ошибка отправки ответа на сообщение %s: %s",
                dto.message_id,
                e,
                exc_info=True,
            )
            raise MessageSendError(user_message)

        chat = None
        try:
            work_chat = await self.chat_service.get_chat_with_archive(
                chat_tgid=dto.chat_tgid,
            )
            archive_chat_id = work_chat.archive_chat_id if work_chat else None
            if archive_chat_id:
                chat = await self.chat_service.get_chat(chat_tgid=dto.chat_tgid)
                chat_title = chat.title if chat else str(dto.chat_tgid)

                chat_id_str = str(dto.chat_tgid).replace("-100", "")
                message_link = f"https://t.me/c/{chat_id_str}/{sent_message_id}"

                when_str = TimeZoneService.now().strftime("%d.%m.%Y %H:%M")
                admin_display = (
                    f"@{dto.admin_username}"
                    if dto.admin_username
                    else f"ID:{dto.admin_tgid}"
                )
                report_text = (
                    f"💬 <b>Ответ на сообщение</b>\n\n"
                    f"Кто: {admin_display}\n"
                    f"Когда: {when_str}\n"
                    f"Чат: {chat_title}\n"
                    f"Ссылка на сообщ: <a href='{message_link}'>ссылка</a>"
                )

                try:
                    await self.bot_message_service.send_chat_message(
                        chat_tgid=archive_chat_id,
                        text=report_text,
                    )
                except (TelegramBadRequest, TelegramForbiddenError) as e:
                    logger.warning(
                        "Не удалось отправить отчет в архивный чат %s: %s",
                        archive_chat_id,
                        e,
                    )
        except (BotBaseException, TelegramAPIError) as e:
            logger.debug("Архивные чаты не найдены или ошибка: %s", e)

        # Логируем действие после успешной отправки ответа
        if self._admin_action_log_service:
            if not chat:
                chat = await self.chat_service.get_chat(chat_tgid=dto.chat_tgid)
            details = f"Чат: {chat.title if chat else dto.chat_tgid}"
            await self._admin_action_log_service.log_action(
                admin_tg_id=dto.admin_tgid,
                action_type=AdminActionType.REPLY_MESSAGE,
                details=details,
            )
