from dataclasses import dataclass
from datetime import datetime

from constants.enums import AdminActionType
from dto.daily_activity import ChatDailyStatsDTO
from repositories import ChatRepository, MessageRepository, UserRepository
from repositories.reaction_repository import MessageReactionRepository
from services import AdminActionLogService, BotPermissionService
from utils.date_utils import validate_and_normalize_period


@dataclass
class UserActivity:
    total_users: int
    active_users: int


class GetDailyTopUsersUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        message_repository: MessageRepository,
        chat_repository: ChatRepository,
        reaction_repository: MessageReactionRepository,
        bot_permission_service: BotPermissionService,
        admin_action_log_service: AdminActionLogService,
    ):
        self._user_repository = user_repository
        self._message_repository = message_repository
        self._chat_repository = chat_repository
        self._reaction_repository = reaction_repository
        self._bot_permission_service = bot_permission_service
        self._admin_action_log_service = admin_action_log_service

    async def execute(
        self,
        chat_id: int,
        admin_tg_id: str,
        date: datetime | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> ChatDailyStatsDTO:
        """
        Получает топ активных пользователей за период в чате.

        Args:
            chat_id: ID чата
            date: Конкретная дата (если указана, анализируется за этот день)
            start_date: Начало периода
            end_date: Конец периода

        Returns:
            ChatDailyStatsDTO с топом пользователей и общей статистикой
        """
        start_date, end_date = validate_and_normalize_period(date, start_date, end_date)

        # Получаем информацию о чате
        chat = await self._chat_repository.get_chat_by_id(chat_id)
        chat_title = chat.title if chat else "Неизвестный чат"

        # Получаем топ пользователей
        top_users = await self._message_repository.get_daily_top_users(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
            limit=10,
        )

        # Получаем топ по реакциям
        top_reactors = await self._reaction_repository.get_daily_top_reactors(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
            limit=10,
        )

        # Получаем популярные реакции
        popular_reactions = await self._reaction_repository.get_daily_popular_reactions(
            chat_id=chat_id,
            start_date=start_date,
            end_date=end_date,
            limit=10,
        )

        # Получаем информацию об активности (активные / всего участников)
        activity_info = await self._get_chat_activity_info(
            chat_tgid=chat.chat_id if chat else str(chat_id),
            chat_db_id=chat_id,
            start_date=start_date,
            end_date=end_date,
        )

        # Подсчитываем общую статистику
        total_messages = sum(user.message_count for user in top_users)
        total_reactions = sum(user.reaction_count for user in top_reactors)

        # Логируем действие администратора
        details = f"Чат: {chat_title} ({chat_id}), Период: {start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
        await self._admin_action_log_service.log_action(
            admin_tg_id=admin_tg_id,
            action_type=AdminActionType.GET_CHAT_DAILY_RATING,
            details=details,
        )

        return ChatDailyStatsDTO(
            chat_id=chat_id,
            chat_title=chat_title,
            start_date=start_date,
            end_date=end_date,
            top_users=top_users,
            top_reactors=top_reactors,
            popular_reactions=popular_reactions,
            total_messages=total_messages,
            total_reactions=total_reactions,
            active_users_count=activity_info.active_users,
            total_users_count=activity_info.total_users,
        )

    async def _get_chat_activity_info(
        self,
        chat_tgid: str,
        chat_db_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> UserActivity:
        """
        Получает общее количество активных пользователей
        и количество участников в чате.
        """
        activity_users = await self._user_repository.total_active_users(
            chat_id=chat_db_id,
            start_date=start_date,
            end_date=end_date,
        )

        total_users = await self._bot_permission_service.get_total_members(
            chat_tgid=chat_tgid
        )

        return UserActivity(total_users=total_users, active_users=activity_users)
