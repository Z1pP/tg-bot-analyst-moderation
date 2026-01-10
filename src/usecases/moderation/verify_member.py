import logging
from typing import Tuple

from services.messaging.bot_message_service import BotMessageService
from services.permissions import BotPermissionService
from utils.antibot_utils import decode_antibot_params

logger = logging.getLogger(__name__)


class VerifyMemberUseCase:
    """
    UseCase для верификации пользователя через личные сообщения.
    """

    def __init__(
        self,
        bot_message_service: BotMessageService,
        bot_permission_service: BotPermissionService,
    ):
        self.bot_message_service = bot_message_service
        self.bot_permission_service = bot_permission_service

    async def execute(
        self,
        payload: str,
        clicking_user_id: int,
    ) -> Tuple[bool, str | None]:
        """
        Проверяет полезную нагрузку и размучивает пользователя.

        Args:
            payload: Строка из аргумента start
            clicking_user_id: ID пользователя, который нажал старт

        Returns:
            (Успех, ID чата или None)
        """
        chat_id, target_user_id = decode_antibot_params(payload)

        if not chat_id or target_user_id != clicking_user_id:
            logger.warning(
                "Попытка верификации с неверными данными: payload=%s, user=%s",
                payload,
                clicking_user_id,
            )
            return False, None

        # Проверяем права бота на модерацию
        can_moderate = await self.bot_permission_service.can_moderate(chat_tgid=chat_id)
        if not can_moderate:
            logger.warning(
                "Бот не имеет прав модератора в чате %s. Невозможно размутить пользователя %s.",
                chat_id,
                target_user_id,
            )
            return False, chat_id

        # Снимаем ограничения
        success = await self.bot_message_service.unmute_chat_member(
            chat_tg_id=chat_id,
            user_tg_id=target_user_id,
        )

        if success:
            logger.info(
                "Пользователь %s успешно прошел верификацию в чате %s",
                target_user_id,
                chat_id,
            )
            return True, chat_id

        return False, chat_id
