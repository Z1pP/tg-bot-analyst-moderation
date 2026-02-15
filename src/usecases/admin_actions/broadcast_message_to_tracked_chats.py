"""Use case: рассылка сообщения во все отслеживаемые чаты администратора."""

import logging

from dto.message_action import BroadcastResultDTO, SendMessageDTO
from exceptions.moderation import MessageSendError
from usecases.admin_actions.send_message_to_chat import SendMessageToChatUseCase
from usecases.chat_tracking.get_user_tracked_chats import GetUserTrackedChatsUseCase

logger = logging.getLogger(__name__)


class BroadcastMessageToTrackedChatsUseCase:
    """Рассылает сообщение админа во все его отслеживаемые чаты."""

    def __init__(
        self,
        get_user_tracked_chats: GetUserTrackedChatsUseCase,
        send_message_to_chat: SendMessageToChatUseCase,
    ):
        self._get_user_tracked_chats = get_user_tracked_chats
        self._send_message_to_chat = send_message_to_chat

    async def execute(
        self,
        admin_tgid: str,
        admin_username: str,
        admin_message_id: int,
    ) -> BroadcastResultDTO:
        """
        Отправляет сообщение во все отслеживаемые чаты администратора.

        Args:
            admin_tgid: Telegram ID администратора.
            admin_username: Username администратора.
            admin_message_id: ID сообщения в чате админа (контент для копирования).

        Returns:
            BroadcastResultDTO с количеством успешных и неуспешных отправок.
        """
        user_chats_dto = await self._get_user_tracked_chats.execute(tg_id=admin_tgid)
        chats = user_chats_dto.chats

        if not chats:
            return BroadcastResultDTO(success_count=0, failed_count=0)

        success_count = 0
        failed_count = 0

        for chat in chats:
            dto = SendMessageDTO(
                chat_tgid=chat.tg_id,
                admin_tgid=admin_tgid,
                admin_username=admin_username,
                admin_message_id=admin_message_id,
            )
            try:
                await self._send_message_to_chat.execute(dto)
                success_count += 1
            except MessageSendError as e:
                logger.warning(
                    "Не удалось отправить сообщение в чат %s: %s",
                    chat.tg_id,
                    e,
                )
                failed_count += 1
            except Exception as e:
                logger.error(
                    "Ошибка отправки сообщения в чат %s: %s",
                    chat.tg_id,
                    e,
                    exc_info=True,
                )
                failed_count += 1

        return BroadcastResultDTO(
            success_count=success_count,
            failed_count=failed_count,
        )
