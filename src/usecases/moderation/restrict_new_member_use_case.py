import logging
from typing import Optional

from services import ChatService
from services.messaging.bot_message_service import BotMessageService
from services.permissions import BotPermissionService
from utils.antibot_utils import encode_antibot_params

logger = logging.getLogger(__name__)


class RestrictNewMemberUseCase:
    """
    UseCase для ограничения нового участника и генерации ссылки на антибот.
    """

    def __init__(
        self,
        bot_message_service: BotMessageService,
        bot_permission_service: BotPermissionService,
        chat_service: ChatService,
    ):
        self.bot_message_service = bot_message_service
        self.bot_permission_service = bot_permission_service
        self.chat_service = chat_service

    async def execute(
        self,
        chat_tgid: str,
        user_id: int,
        bot_username: str,
    ) -> Optional[str]:
        """
        Проверяет настройки чата, мьютит пользователя и возвращает ссылку для верификации.

        Args:
            chat_tgid: Telegram ID чата
            user_id: Telegram ID пользователя
            bot_username: Username бота для генерации ссылки

        Returns:
            Ссылка на верификацию или None, если антибот выключен
        """
        chat = await self.chat_service.get_chat(chat_tgid=chat_tgid)

        if not chat or not chat.is_antibot_enabled:
            return None

        # Проверяем права бота на модерацию
        can_moderate = await self.bot_permission_service.can_moderate(
            chat_tgid=chat_tgid
        )

        if not can_moderate:
            logger.warning(
                "Бот не имеет прав модератора в чате %s. Антибот не может ограничить пользователя.",
                chat_tgid,
            )
            return None

        # Мьютим пользователя (0 = бессрочно до ручного изменения)
        success = await self.bot_message_service.mute_chat_member(
            chat_tg_id=chat_tgid,
            user_tg_id=user_id,
            duration_seconds=0,
        )

        if not success:
            logger.error(
                "Не удалось ограничить пользователя %s в чате %s для антибот-проверки",
                user_id,
                chat_tgid,
            )
            return None

        # Генерируем ссылку
        payload = encode_antibot_params(chat_tgid, user_id)
        return f"https://t.me/{bot_username}?start={payload}"
