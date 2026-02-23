import logging

from services.messaging.bot_message_service import BotMessageService
from services.permissions import BotPermissionService

logger = logging.getLogger(__name__)


class VerifyMemberUseCase:
    """
    UseCase для верификации пользователя через нажатие кнопки в групповом чате.
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
        user_id: int,
        chat_id: str,
    ) -> bool:
        """
        Снимает мут с пользователя, прошедшего антибот-проверку.

        Args:
            user_id: Telegram ID верифицированного пользователя
            chat_id: Telegram ID чата

        Returns:
            True если мут успешно снят
        """
        can_moderate = await self.bot_permission_service.can_moderate(chat_tgid=chat_id)
        if not can_moderate:
            logger.warning(
                "Бот не имеет прав модератора в чате %s. Невозможно размутить пользователя %s.",
                chat_id,
                user_id,
            )
            return False

        success = await self.bot_message_service.unmute_chat_member(
            chat_tg_id=chat_id,
            user_tg_id=user_id,
        )

        if success:
            logger.info(
                "Пользователь %s успешно прошел антибот-верификацию в чате %s",
                user_id,
                chat_id,
            )

        return success
