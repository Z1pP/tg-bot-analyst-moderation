from datetime import datetime

from dto import MessageReactionDTO
from dto.buffer import BufferedReactionDTO
from models import MessageReaction
from services.analytics_buffer_service import AnalyticsBufferService


class SaveMessageReactionUseCase:
    def __init__(self, buffer_service: AnalyticsBufferService):
        self.buffer_service = buffer_service

    async def execute(self, reaction_dto: MessageReactionDTO) -> MessageReaction:
        """
        Сохраняет реакцию в буфер Redis для последующей батч-обработки.

        Возвращает "заглушку" MessageReaction, так как реакция еще не сохранена в БД.
        ID будет присвоен после обработки воркером.
        """
        # Конвертируем MessageReactionDTO в BufferedReactionDTO
        buffered_dto = BufferedReactionDTO(
            chat_id=reaction_dto.chat_id,
            user_id=reaction_dto.user_id,
            message_id=reaction_dto.message_id,
            action=reaction_dto.action.value,  # Конвертируем enum в строку
            emoji=reaction_dto.emoji,
            message_url=reaction_dto.message_url,
            created_at=reaction_dto.created_at or datetime.now(),
        )

        # Добавляем в буфер Redis
        await self.buffer_service.add_reaction(buffered_dto)

        # Возвращаем заглушку (ID будет присвоен после обработки воркером)
        return MessageReaction(
            id=0,  # Временное значение
            chat_id=reaction_dto.chat_id,
            user_id=reaction_dto.user_id,
            message_id=reaction_dto.message_id,
            action=reaction_dto.action,
            emoji=reaction_dto.emoji,
            message_url=reaction_dto.message_url,
        )
