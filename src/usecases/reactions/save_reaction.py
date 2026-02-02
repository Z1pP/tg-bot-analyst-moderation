from datetime import datetime

from dto import MessageReactionDTO
from dto.buffer import BufferedReactionDTO
from models import MessageReaction
from services.analytics_buffer_service import AnalyticsBufferService
from services.chat.chat_service import ChatService
from services.user.user_service import UserService


class SaveMessageReactionUseCase:
    def __init__(
        self,
        buffer_service: AnalyticsBufferService,
        user_service: UserService,
        chat_service: ChatService,
    ):
        self.buffer_service = buffer_service
        self.user_service = user_service
        self.chat_service = chat_service

    async def execute(self, reaction_dto: MessageReactionDTO) -> MessageReaction:
        """
        Сохраняет реакцию в буфер Redis для последующей батч-обработки.

        Возвращает "заглушку" MessageReaction, так как реакция еще не сохранена в БД.
        ID будет присвоен после обработки воркером.
        """
        # Разрешаем Telegram ID в записи БД
        user = await self.user_service.get_or_create(
            tg_id=reaction_dto.user_tgid,
            username=reaction_dto.user_username,
        )
        chat = await self.chat_service.get_or_create(
            chat_tgid=reaction_dto.chat_tgid,
        )

        # Конвертируем MessageReactionDTO в BufferedReactionDTO
        buffered_dto = BufferedReactionDTO(
            chat_id=chat.id,
            user_id=user.id,
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
            chat_id=chat.id,
            user_id=user.id,
            message_id=reaction_dto.message_id,
            action=reaction_dto.action,
            emoji=reaction_dto.emoji,
            message_url=reaction_dto.message_url,
        )
