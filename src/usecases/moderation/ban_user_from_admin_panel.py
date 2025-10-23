import logging

from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from constants.punishment import PunishmentType
from dto import AdminPanelBanDTO
from exceptions.moderation import BotInsufficientPermissionsError
from repositories.user_chat_status_repository import UserChatStatusRepository
from services import (
    BotMessageService,
    BotPermissionService,
    ChatService,
    UserService,
)

from .base import ModerationUseCase

logger = logging.getLogger(__name__)


class BanUserFromAdminPanelUseCase(ModerationUseCase):
    """
    Use case для блокировки пользователя через админ-панель бота.
    """

    def __init__(
        self,
        user_service: UserService,
        bot_message_service: BotMessageService,
        chat_service: ChatService,
        user_chat_status_repository: UserChatStatusRepository,
        permission_service: BotPermissionService,
    ):
        super().__init__(
            user_service,
            bot_message_service,
            chat_service,
            user_chat_status_repository,
            permission_service,
        )

    async def execute(self, dto: AdminPanelBanDTO) -> None:
        """Выполняет блокировку пользователя через админ-панель."""
        logger.info(
            "Начало блокировки пользователя %s в чате %s админом %s",
            dto.user_tgid,
            dto.chat_tgid,
            dto.admin_tgid,
        )

        violator = await self.user_service.get_user(
            tg_id=dto.user_tgid,
            username=dto.user_username,
        )
        chat = await self.chat_service.get_chat(
            chat_id=dto.chat_tgid,
            title=dto.chat_title,
        )

        archive_chats = await self.chat_service.get_archive_chats(
            source_chat_tgid=dto.chat_tgid,
        )

        if not archive_chats:
            logger.warning(
                "Отсутствуют архивные чаты для %s, блокировка невозможна",
                dto.chat_tgid,
            )
            raise BotInsufficientPermissionsError(chat_title=dto.chat_title)

        await self.user_chat_status_repository.get_or_create(
            user_id=violator.id,
            chat_id=chat.id,
        )

        try:
            is_success = await self.bot_message_service.apply_punishmnet(
                chat_tg_id=chat.chat_id,
                user_tg_id=violator.tg_id,
                action=PunishmentType.BAN,
            )
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.error(
                "Telegram API ошибка при бане %s в чате %s: %s",
                violator.tg_id,
                chat.chat_id,
                e,
                exc_info=True,
            )
            raise BotInsufficientPermissionsError(chat_title=dto.chat_title)

        if not is_success:
            logger.error(
                "Не удалось забанить пользователя %s в чате %s",
                violator.tg_id,
                chat.chat_id,
            )
            raise BotInsufficientPermissionsError(chat_title=dto.chat_title)

        await self.user_chat_status_repository.update_status(
            user_id=violator.id,
            chat_id=chat.id,
            is_banned=True,
        )
        logger.info("Статус пользователя %s обновлен: is_banned=True", violator.tg_id)

        ban_message = (
            f"🚫 @{dto.user_username}, ты часто нарушал правила чата, "
            f"поэтому мы были вынуждены закрыть для тебя доступ. "
            f"Захочешь вернуться - обсуди это с модераторами и/или администраторами."
        )
        try:
            await self.bot_message_service.send_chat_message(
                chat_tgid=chat.chat_id,
                text=ban_message,
            )
            logger.info("Сообщение о бане отправлено в чат %s", chat.chat_id)
        except (TelegramBadRequest, TelegramForbiddenError) as e:
            logger.warning(
                "Не удалось отправить сообщение о бане в чат %s: %s",
                chat.chat_id,
                e,
            )

        report_text = (
            f"🚫 <b>Пользователь заблокирован</b>\n\n"
            f"• Юзер: @{dto.user_username}\n"
            f"• ID: {dto.user_tgid}\n"
            f"• Причина: {dto.reason}\n"
            f"• Заблокировал: @{dto.admin_username}\n"
            f"• Чат: {dto.chat_title}"
        )

        for archive_chat in archive_chats:
            try:
                await self.bot_message_service.send_chat_message(
                    chat_tgid=archive_chat.chat_id,
                    text=report_text,
                )
                logger.debug(
                    "Отчет отправлен в архивный чат %s",
                    archive_chat.chat_id,
                )
            except (TelegramBadRequest, TelegramForbiddenError) as e:
                logger.error(
                    "Не удалось отправить отчет в архивный чат %s: %s",
                    archive_chat.chat_id,
                    e,
                    exc_info=True,
                )

        logger.info(
            "Блокировка пользователя %s в чате %s завершена успешно",
            dto.user_tgid,
            dto.chat_tgid,
        )
