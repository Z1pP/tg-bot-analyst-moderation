from collections import defaultdict

from dto.report import DailyReportDTO
from models import ChatMessage, User
from repositories import MessageRepository, UserRepository


class GetDailyReportUseCase:
    def __init__(
        self,
        user_repository: UserRepository,
        message_repository: MessageRepository,
    ):
        self._user_repository = user_repository
        self._message_repository = message_repository

    async def execute(self, daily_report_dto: DailyReportDTO) -> str:
        """
        Получает отчет о количестве сообщений за день для указанного пользователя.
        """

        try:
            # Получаем пользователя из репозитория
            user = await self._user_repository.get_user_by_username(
                username=daily_report_dto.username
            )
            if user is None:
                return (
                    f"Модератор в таким именем - {daily_report_dto.username} не найден."
                )

            # Получаем все сооббщения пользователя за день
            messages = await self._message_repository.get_messages_by_period(
                user_id=user.id,
                start_date=daily_report_dto.start_date,
                end_date=daily_report_dto.end_date,
            )

            return self._format_report(messages=messages, user=user)
        except Exception as e:
            return f"Произошла ошибка при получении отчета: {str(e)}"

    def _format_report(self, messages: list[ChatMessage], user: User) -> str:
        """
        Форматирует отчет о количестве сообщений за день.
        """
        if not messages:
            return "❌ Нет данных для формирования отчета."

        # Группируем сообщения по датам и чатам
        date_chat_stats = defaultdict(lambda: defaultdict(int))

        for message in messages:
            date_key = message.created_at.date()
            chat_title = message.chat_session.title
            date_chat_stats[date_key][chat_title] += 1

        # Сортируем даты в хронологическом порядке
        sorted_dates = sorted(date_chat_stats.keys())

        # Формируем заголовок отчета
        report = (
            f"📅 <b>Отчет о сообщениях</b>\n"
            f"👤 Модератор: <b>{user.username}</b>\n"
            f"📊 Всего сообщений: <b>{len(messages)}</b>\n"
            "────────────────────────────\n"
        )

        # Добавляем данные по каждой дате
        for date in sorted_dates:
            report += f"\n📅 <b>{date.strftime('%d.%m.%Y')}</b>\n"
            for chat_title, count in date_chat_stats[date].items():
                report += f"  • «{chat_title}» — <b>{count}</b>\n"

        # Итоговый разделитель
        report += "────────────────────────────\n"
        return report
