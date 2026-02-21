import logging

from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
)
from exceptions import BotBaseException

from constants.enums import AdminActionType
from dto.message_action import MessageActionDTO
from exceptions.moderation import MessageDeleteError, MessageSendError
from services import AdminActionLogService, BotMessageService, ChatService

logger = logging.getLogger(__name__)


class DeleteMessageUseCase:
    """UseCase для удаления сообщения из чата."""

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
        """Удаляет сообщение из чата."""
        logger.info(
            "Удаление сообщения %s из чата %s админом %s",
            dto.message_id,
            dto.chat_tgid,
            dto.admin_tgid,
        )

        work_chat = await self.chat_service.get_chat_with_archive(
            chat_tgid=dto.chat_tgid,
        )

        archive_chat_id = work_chat.archive_chat_id if work_chat else None
        if archive_chat_id:
            try:
                await self.bot_message_service.forward_message(
                    chat_tgid=archive_chat_id,
                    from_chat_tgid=dto.chat_tgid,
                    message_tgid=dto.message_id,
                )
                logger.debug(
                    "Сообщение %s переслано в архивный чат %s",
                    dto.message_id,
                    archive_chat_id,
                )
            except TelegramAPIError as e:
                logger.warning(
                    "Не удалось переслать сообщение в архивный чат %s: %s",
                    archive_chat_id,
                    e,
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

        if archive_chat_id:
            try:
                chat = await self.chat_service.get_chat(chat_tgid=dto.chat_tgid)
                chat_title = chat.title if chat else str(dto.chat_tgid)
                report_text = (
                    f"🗑 <b>Удалено сообщение ботом</b>\n\n"
                    f"Чат: {chat_title}\n"
                    f"Кто удалил: @{dto.admin_username}"
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
                logger.debug("Ошибка отправки отчета: %s", e)

        # Логируем действие после успешного удаления сообщения
        if self._admin_action_log_service:
            await self._admin_action_log_service.log_action(
                admin_tg_id=dto.admin_tgid,
                action_type=AdminActionType.DELETE_MESSAGE,
            )
