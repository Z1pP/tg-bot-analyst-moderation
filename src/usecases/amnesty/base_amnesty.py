import logging
from typing import List

from dto import ChatDTO
from exceptions.moderation import ArchiveChatError, BotInsufficientPermissionsError
from models.chat_session import ChatSession
from services import BotMessageService, BotPermissionService, ChatService

logger = logging.getLogger(__name__)


class BaseAmnestyUseCase:
    """Базовый UseCase для операций амнистии с общей логикой проверок и отправки отчётов."""

    def __init__(
        self,
        bot_message_service: BotMessageService,
        bot_permission_service: BotPermissionService,
        chat_service: ChatService,
    ):
        self.bot_message_service = bot_message_service
        self.bot_permission_service = bot_permission_service
        self.chat_service = chat_service

    async def _validate_and_get_archive_chats(self, chat: ChatDTO) -> List[ChatSession]:
        """
        Проверяет права модерации и получает архивные чаты.

        Args:
            chat: DTO чата

        Returns:
            Список архивных чатов

        Raises:
            BotInsufficientPermissionsError: Если бот не может модерировать
            ArchiveChatError: Если архивные чаты не найдены
        """
        can_moderate = await self.bot_permission_service.can_moderate(
            chat_tgid=chat.tg_id
        )

        if not can_moderate:
            raise BotInsufficientPermissionsError(chat_title=chat.title)

        archive_chats = await self.chat_service.get_chat_with_archive(
            chat_tgid=chat.tg_id,
        )

        if not archive_chats:
            raise ArchiveChatError(chat_title=chat.title)

        return archive_chats

    async def _send_report_to_archives(
        self, archive_chats: List[ChatSession], report_text: str
    ) -> None:
        """
        Отправляет отчёт во все архивные чаты.

        Args:
            archive_chats: Список архивных чатов
            report_text: Текст отчёта
        """
        for archive_chat in archive_chats:
            await self.bot_message_service.send_chat_message(
                chat_tgid=archive_chat.chat_id,
                text=report_text,
            )
