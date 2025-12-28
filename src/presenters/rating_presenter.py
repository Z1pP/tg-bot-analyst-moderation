from constants import Dialog
from dto.daily_activity import (
    ChatDailyStatsDTO,
    PopularReactionDTO,
    UserDailyActivityDTO,
    UserReactionActivityDTO,
)


class RatingPresenter:
    """Презентер для форматирования рейтинга пользователей."""

    RANK_EMOJIS = {
        1: "🥇",
        2: "🥈",
        3: "🥉",
        4: "🏅",
        5: "🎖️",
        6: "🏵️",
        7: "🎗️",
        8: "🌟",
        9: "⭐",
        10: "✨",
    }

    @classmethod
    def format_daily_rating(cls, stats: ChatDailyStatsDTO) -> str:
        """
        Форматирует дневной рейтинг пользователей.

        Args:
            stats: Статистика чата за период

        Returns:
            Отформатированная строка с рейтингом
        """
        period_str, title = cls._get_period_info(stats)

        if not stats.top_users:
            return (
                f"{title}\n"
                f"📅 {period_str} | 💬 <b>{stats.chat_title}</b>\n\n"
                f"{Dialog.Rating.NO_ACTIVITY}"
            )

        sections = [
            cls._format_header(stats, period_str, title),
            cls._format_top_users(stats.top_users),
            cls._format_top_reactors(stats.top_reactors),
            cls._format_popular_reactions(stats.popular_reactions),
            cls._format_summary(stats),
        ]

        # Фильтруем пустые секции и соединяем
        return "\n".join(filter(None, sections))

    @classmethod
    def _get_period_info(cls, stats: ChatDailyStatsDTO) -> tuple[str, str]:
        """Возвращает строку периода и заголовок."""
        if stats.end_date and stats.start_date.date() != stats.end_date.date():
            period_str = f"{stats.start_date.strftime('%d.%m.%Y')} - {stats.end_date.strftime('%d.%m.%Y')}"
            title = Dialog.Rating.TOP_ACTIVE_PERIOD
        else:
            period_str = stats.start_date.strftime("%Y-%m-%d")
            title = Dialog.Rating.TOP_ACTIVE_DAILY
        return period_str, title

    @classmethod
    def _format_header(
        cls, stats: ChatDailyStatsDTO, period_str: str, title: str
    ) -> str:
        """Форматирует заголовок рейтинга."""
        return (
            f"{title}\n"
            f"📅 {period_str} | 💬 <b>{stats.chat_title}</b>\n\n"
            f"{Dialog.Rating.ACTIVE_USERS} {stats.active_users_count} из {stats.total_users_count}\n"
        )

    @classmethod
    def _format_top_users(cls, top_users: list[UserDailyActivityDTO]) -> str:
        """Форматирует топ по сообщениям."""
        if not top_users:
            return ""

        text = f"\n{Dialog.Rating.BY_MESSAGES}\n"
        for user in top_users:
            emoji = cls.RANK_EMOJIS.get(user.rank, "💫")
            username = cls._get_username(user.username)
            text += f"{emoji} {username} — {user.message_count} сообщ.\n"
        return text

    @classmethod
    def _format_top_reactors(cls, top_reactors: list[UserReactionActivityDTO]) -> str:
        """Форматирует топ по реакциям."""
        if not top_reactors:
            return ""

        text = f"\n{Dialog.Rating.BY_REACTIONS}\n"
        for user in top_reactors:
            emoji = cls.RANK_EMOJIS.get(user.rank, "💫")
            username = cls._get_username(user.username)
            text += f"{emoji} {username} — {user.reaction_count} реакт.\n"
        return text

    @classmethod
    def _format_popular_reactions(
        cls, popular_reactions: list[PopularReactionDTO]
    ) -> str:
        """Форматирует популярные реакции."""
        if not popular_reactions:
            return ""

        text = f"\n{Dialog.Rating.POPULAR_REACTIONS}\n"
        for reaction in popular_reactions:
            text += f"{reaction.emoji} — {reaction.count} раз\n"
        return text

    @classmethod
    def _format_summary(cls, stats: ChatDailyStatsDTO) -> str:
        """Форматирует итоговую статистику."""
        return (
            f"\n{Dialog.Rating.TOTAL_MESSAGES} {stats.total_messages}\n"
            f"{Dialog.Rating.TOTAL_REACTIONS} {stats.total_reactions}"
        )

    @staticmethod
    def _get_username(username: str) -> str:
        """Форматирует имя пользователя."""
        if username != "Без имени" and not username.startswith("User ID:"):
            return f"@{username}"
        return f"👤 {username}"
