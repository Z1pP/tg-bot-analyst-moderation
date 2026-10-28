"""Use case для проверки и запуска автомодерации."""

import logging

from dto.automoderation import AutoModerationRunDTO, CheckAndRunAutoModerationDTO
from services.chat import ChatService
from usecases.automoderation.run_auto_moderation_on_message import (
    RunAutoModerationOnMessageUseCase,
)

logger = logging.getLogger(__name__)


class CheckAndRunAutoModerationUseCase:
    """Проверяет настройку автомодерации чата и запускает обработку сообщения.

    Вся бизнес-логика проверки находится здесь, хендлер только передаёт DTO.
    Ошибки логируются и не пробрасываются наружу, чтобы не ломать обработку сообщений.
    """

    def __init__(
        self,
        chat_service: ChatService,
        run_auto_moderation_usecase: RunAutoModerationOnMessageUseCase,
    ) -> None:
        self._chat_service = chat_service
        self._run_auto_moderation = run_auto_moderation_usecase

    async def execute(self, dto: CheckAndRunAutoModerationDTO) -> None:
        """Запускает автомодерацию, если она включена для чата."""
        if not dto.message_text:
            return

        try:
            chat = await self._chat_service.get_chat(
                chat_tgid=dto.chat_tgid,
                title=dto.chat_title,
            )
            if not chat or not chat.is_auto_moderation_enabled:
                return

            await self._run_auto_moderation.execute(
                AutoModerationRunDTO(
                    chat_tgid=dto.chat_tgid,
                    chat_title=chat.title or "",
                    is_auto_moderation_enabled=True,
                    archive_chat_tgid=chat.archive_chat_id,
                    username=dto.username,
                    user_tg_id=dto.user_tg_id,
                    message_id=dto.message_id,
                    message_text=dto.message_text,
                )
            )
        except Exception:
            logger.exception(
                "automod: непойманная ошибка после сообщения chat_id=%s",
                dto.chat_tgid,
            )