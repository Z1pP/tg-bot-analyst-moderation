from constants import Dialog
from dto.daily_activity import (
    ChatDailyStatsDTO,
    PopularReactionDTO,
    UserDailyActivityDTO,
    UserReactionActivityDTO,
)


class RatingPresenter:
    """Презентер для форматирования рейтинга пользователей."""

    @classmethod
    def format_daily_rating(cls, stats: ChatDailyStatsDTO) -> str:
        """
        Форматирует дневной рейтинг пользователей.

        Args:
            stats: Статистика чата за период

        Returns:
            Отформатированная строка с рейтингом
        """
        period_str = cls._get_period_string(stats)
        chat_name = f"<b>{stats.chat_title}</b>" if stats.chat_title else "чате"

        if not stats.top_users and not stats.top_reactors:
            has_membership_stats = bool(
                stats.joins_count or stats.left_count or stats.removed_count
            )
            if has_membership_stats:
                header = cls._format_header(stats, period_str, chat_name)
                return f"{header}\n\n{Dialog.Rating.NO_ACTIVITY}"

            title = Dialog.Rating.RATING_TITLE.format(
                period=period_str, chat_name=chat_name
            )
            return f"{title}\n\n{Dialog.Rating.NO_ACTIVITY}"

        header = cls._format_header(stats, period_str, chat_name)
        top_messages = cls._format_top_users(stats.top_users[:10])
        top_reactions = cls._format_top_reactors(stats.top_reactors[:5])
        popular_reactions = cls._format_popular_reactions(stats.popular_reactions[:7])

        sections = [header, top_messages, top_reactions, popular_reactions]

        # Filter out empty strings and join with double newlines for clear separation
        return "\n\n".join(filter(None, sections))

    @classmethod
    def _get_period_string(cls, stats: ChatDailyStatsDTO) -> str:
        """Возвращает строку периода."""
        start_fmt = stats.start_date.strftime("%d.%m.%Y")
        if stats.end_date and stats.start_date.date() != stats.end_date.date():
            end_fmt = stats.end_date.strftime("%d.%m.%Y")
            return f"{start_fmt}-{end_fmt}"
        return start_fmt

    @classmethod
    def _format_header(
        cls, stats: ChatDailyStatsDTO, period_str: str, chat_name: str
    ) -> str:
        """Форматирует заголовок и общую статистику."""
        title = Dialog.Rating.RATING_TITLE.format(
            period=period_str, chat_name=chat_name
        )

        lines = [
            title,
            "",
            f"{Dialog.Rating.ACTIVE_USERS} {stats.active_users_count} из {stats.total_users_count}",
            f"{Dialog.Rating.TOTAL_MESSAGES} {stats.total_messages}",
            f"{Dialog.Rating.TOTAL_REACTIONS} {stats.total_reactions}",
            f"{Dialog.Rating.JOINS_COUNT} {stats.joins_count}",
            f"{Dialog.Rating.LEFT_COUNT} {stats.left_count}",
            f"{Dialog.Rating.REMOVED_COUNT} {stats.removed_count}",
        ]
        return "\n".join(lines)

    @classmethod
    def _format_top_users(cls, top_users: list[UserDailyActivityDTO]) -> str:
        """Форматирует топ по сообщениям."""
        if not top_users:
            return ""

        lines = [Dialog.Rating.TOP_USERS_BY_MESSAGES]
        for i, user in enumerate(top_users, 1):
            username = cls._get_username(user.username)
            lines.append(f"{i}. {username} — {user.message_count} сообщ.")
        return "\n".join(lines)

    @classmethod
    def _format_top_reactors(cls, top_reactors: list[UserReactionActivityDTO]) -> str:
        """Форматирует топ по реакциям."""
        if not top_reactors:
            return ""

        lines = [Dialog.Rating.TOP_USERS_BY_REACTIONS]
        for i, user in enumerate(top_reactors, 1):
            username = cls._get_username(user.username)
            lines.append(f"{i}. {username} — {user.reaction_count} реакций")
        return "\n".join(lines)

    @classmethod
    def _format_popular_reactions(
        cls, popular_reactions: list[PopularReactionDTO]
    ) -> str:
        """Форматирует популярные реакции."""
        if not popular_reactions:
            return ""

        lines = [Dialog.Rating.TOP_REACTIONS_LIST]
        for i, reaction in enumerate(popular_reactions, 1):
            lines.append(f"{i}. {reaction.emoji} — {reaction.count} раз")
        return "\n".join(lines)

    @staticmethod
    def _get_username(username: str) -> str:
        """Форматирует имя пользователя."""
        if username != "Без имени" and not username.startswith("User ID:"):
            return f"@{username}"
        return f"👤 {username}"
