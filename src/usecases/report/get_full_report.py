from datetime import datetime, timedelta
from statistics import mean, median

from dto.report import AllModeratorReportDTO
from models import ChatMessage, MessageReply, User
from repositories import MessageReplyRepository, MessageRepository, UserRepository


class GetAllModeratorsReportUseCase:
    def __init__(
        self,
        msg_reply_repository: MessageReplyRepository,
        message_repository: MessageRepository,
        user_repository: UserRepository,
    ):
        self._msg_reply_repository = msg_reply_repository
        self._user_repository = user_repository
        self._message_repository = message_repository

    async def execute(self, dto: AllModeratorReportDTO) -> str:
        users = await self._user_repository.get_all_users()

        reports = []

        if not users:
            raise

        selected_period = self._format_selected_period(dto.selected_period)

        report_title = f"Отчет по модераторам за {selected_period}"

        for user in users:
            replies = await self._msg_reply_repository.get_replies_by_user_and_period(
                user_id=user.id,
                start_date=dto.start_date,
                end_date=dto.end_date,
            )
            messages = await self._message_repository.get_messages_by_period_date(
                user_id=user.id,
                start_date=dto.start_date,
                end_date=dto.end_date,
            )

            if not replies:
                continue

            report = self._generate_report(
                replies=replies,
                messages=messages,
                user=user,
                start_date=dto.start_date,
                end_date=dto.end_date,
            )

            reports.append(report)

        return "\n\n".join([report_title] + reports)

    def _generate_report(
        self,
        replies: list[MessageReply],
        messages: list[ChatMessage],
        user: User,
        start_date: datetime,
        end_date: datetime,
        selected_period: str = None,
    ) -> str:
        """
        Создает отчет для одного модератора
        """

        # Сортируем ответы по времени
        sorted_replies = sorted(replies, key=lambda r: r.created_at)

        response_times = [reply.response_time_seconds for reply in replies]
        total_message = len(messages)
        period_hours = (end_date - start_date).total_seconds() / 3600
        avg_message_per_hour = (
            round(total_message / period_hours, 2) if period_hours else 0
        )

        # Рассчитываем статистику
        avg_time = round(mean(response_times), 2)  # в секундах
        median_time = round(median(response_times), 2)
        min_time = round(min(response_times), 2)
        max_time = round(max(response_times), 2)
        total_replies = len(replies)

        # Поиск перерывов > 30 мин
        breaks = []
        for i in range(1, len(sorted_replies)):
            prev_reply = sorted_replies[i - 1]
            curr_reply = sorted_replies[i]

            time_diff: timedelta = curr_reply.created_at - prev_reply.created_at
            minutes_diff = time_diff.total_seconds() / 60

            if minutes_diff > 30:
                start_break = prev_reply.created_at.strftime("%H:%M")
                end_break = curr_reply.created_at.strftime("%H:%M")
                breaks.append(f"{start_break}-{end_break} — {round(minutes_diff)} мин.")

        # Формируем текст отчета в HTML
        report = [
            f"@{user.username}",
            f"Всего сообщений: <b>{total_message}</b>",
            f"Сред. кол-во сообщ. в час: <b>{avg_message_per_hour:.2f}</b>",
            f"Всего ответов: <b>{total_replies}</b>",
            f"Мин. и макс. время ответа: <b>{min_time} сек.</b> и <b>{max_time / 60:.2f} мин.</b>",
            f"Сред. и медиан. время ответа: <b>{avg_time} сек.</b> и <b>{median_time} сек.</b>",
        ]

        if breaks:
            report.append("Перерывы:")
            for break_info in breaks:
                report.append(f"- {break_info}")
        else:
            report.append("Перерывы: отсутствуют")

        return "\n".join(report)

    def _format_selected_period(self, selected_period: str) -> str:
        """
        Форматирует выбранный период в читаемый формат.
        """
        if not selected_period:
            return "указанный период"
        period = selected_period.split("За")[-1]
        return period.strip()
