from datetime import datetime

from dto.daily_activity import ChatDailyStatsDTO
from repositories import ChatRepository, MessageRepository
from repositories.reaction_repository import MessageReactionRepository


class GetDailyTopUsersUseCase:
    def __init__(
        self,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
        reaction_repository: MessageReactionRepository,
    ):
        self.message_repository = message_repository
        self.chat_repository = chat_repository
        self.reaction_repository = reaction_repository

    async def execute(self, chat_id: int, date: datetime) -> ChatDailyStatsDTO:
        """
        Получает топ активных пользователей за день в чате.

        Args:
            chat_id: ID чата
            date: Дата для анализа

        Returns:
            ChatDailyStatsDTO с топом пользователей и общей статистикой
        """
        # Получаем информацию о чате
        chat = await self.chat_repository.get_chat_by_id(chat_id)
        chat_title = chat.title if chat else "Неизвестный чат"

        # Получаем топ пользователей
        top_users = await self.message_repository.get_daily_top_users(
            chat_id=chat_id,
            date=date,
            limit=10,
        )

        # Получаем топ по реакциям
        top_reactors = await self.reaction_repository.get_daily_top_reactors(
            chat_id=chat_id,
            date=date,
            limit=10,
        )

        # Получаем популярные реакции
        popular_reactions = await self.reaction_repository.get_daily_popular_reactions(
            chat_id=chat_id,
            date=date,
            limit=3,
        )

        # Подсчитываем общую статистику
        total_messages = sum(user.message_count for user in top_users)
        total_reactions = sum(user.reaction_count for user in top_reactors)
        active_users_count = len(top_users)

        return ChatDailyStatsDTO(
            chat_id=chat_id,
            chat_title=chat_title,
            date=date,
            top_users=top_users,
            top_reactors=top_reactors,
            popular_reactions=popular_reactions,
            total_messages=total_messages,
            total_reactions=total_reactions,
            active_users_count=active_users_count,
        )
