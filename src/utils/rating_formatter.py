from dto.daily_activity import ChatDailyStatsDTO


class RatingFormatter:
    """Форматирует рейтинг пользователей для красивого вывода."""

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

    @staticmethod
    def format_daily_rating(stats: ChatDailyStatsDTO) -> str:
        """
        Форматирует дневной рейтинг пользователей.

        Args:
            stats: Статистика чата за день

        Returns:
            Отформатированная строка с рейтингом
        """
        if not stats.top_users:
            return (
                f"🏆 <b>ТОП-10 АКТИВНЫХ ЗА СУТКИ</b>\n"
                f"📅 {stats.date.strftime('%Y-%m-%d')} | 💬 <b>{stats.chat_title}</b>\n\n"
                f"😴 <i>Сегодня никто не писал в чате</i>"
            )

        # Заголовок
        text = (
            f"🏆 <b>ТОП-10 АКТИВНЫХ ЗА СУТКИ</b>\n"
            f"📅 {stats.date.strftime('%Y-%m-%d')} | 💬 <b>{stats.chat_title}</b>\n\n"
        )

        # Рейтинг по сообщениям
        text += "💬 <b>По сообщениям:</b>\n"
        for user in stats.top_users:
            emoji = RatingFormatter.RANK_EMOJIS.get(user.rank, "💫")
            username = (
                f"@{user.username}" if user.username != "Без имени" else "👤 Без имени"
            )
            text += f"{emoji} {username} — {user.message_count} сообщений\n"
        
        # Рейтинг по реакциям
        if stats.top_reactors:
            text += "\n😍 <b>По реакциям:</b>\n"
            for user in stats.top_reactors:
                emoji = RatingFormatter.RANK_EMOJIS.get(user.rank, "💫")
                username = (
                    f"@{user.username}" if user.username != "Без имени" else "👤 Без имени"
                )
                text += f"{emoji} {username} — {user.reaction_count} реакций\n"
        
        # Популярные реакции
        if stats.popular_reactions:
            text += "\n🔥 <b>Популярные реакции:</b>\n"
            for reaction in stats.popular_reactions:
                text += f"{reaction.emoji} — {reaction.count} раз\n"

        # Общая статистика
        text += (
            f"\n📊 <b>Всего сообщений:</b> {stats.total_messages}\n"
            f"😍 <b>Всего реакций:</b> {stats.total_reactions}\n"
            f"👥 <b>Активных пользователей:</b> {stats.active_users_count}"
        )

        return text
