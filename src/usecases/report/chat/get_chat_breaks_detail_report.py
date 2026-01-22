import logging
from typing import List

from constants.dialogs import ReportDialogs
from dto.report import ChatReportDTO
from models import User
from services.break_analysis_service import BreakAnalysisService

from ..base import ChatReportUseCase

logger = logging.getLogger(__name__)


class GetChatBreaksDetailReportUseCase(ChatReportUseCase):
    async def execute(self, dto: ChatReportDTO) -> List[str]:
        """Генерирует детализированный отчет по перерывам для чата."""
        # Получаем отслеживаемых пользователей
        users = await self._user_repository.get_tracked_users_for_admin(
            admin_tg_id=dto.admin_tg_id,
        )

        if not users:
            return ["⚠️ Список пользователей пуст, добавьте пользователя!"]

        # Получаем информацию о чате
        chat = await self._chat_repository.get_chat_by_id(dto.chat_id)
        if not chat:
            return ["⚠️ Чат не найден!"]

        if not self._has_time_settings(chat=chat):
            return [ReportDialogs.CHAT_REPORT_SETTINGS_REQUIRED]

        period = self._format_selected_period(
            start_date=dto.start_date,
            end_date=dto.end_date,
        )

        report_title = f"<b>📊 Детализация перерывов по датам в чате «{chat.title}» за {period}</b>"

        reports = []
        for user in users:
            user_data = await self._get_user_data_for_chat(user=user, dto=dto)

            # Пропускаем пользователей без активности в чате
            if not user_data["messages"] and not user_data["reactions"]:
                continue

            user_report = self._generate_user_breaks_detail(data=user_data, user=user)
            if user_report:
                reports.append(user_report)

        if not reports:
            return [
                f"{report_title}\n\n⚠️ Нет данных для детализации за указанный период"
            ]

        full_report = "\n\n".join([report_title] + reports)
        return self._split_report(full_report)

    async def _get_user_data_for_chat(self, user: User, dto: ChatReportDTO) -> dict:
        """Получает данные пользователя за период в конкретном чате."""
        # Получаем сообщения пользователя в чате
        messages = await self._get_processed_items_by_chat_with_users(
            self._message_repository.get_messages_by_chat_id_and_period,
            dto.chat_id,
            dto.start_date,
            dto.end_date,
            [user.id],
        )

        # Получаем реакции пользователя в чате
        reactions = await self._get_processed_items_by_chat_with_users(
            self._reaction_repository.get_reactions_by_chat_and_period,
            dto.chat_id,
            dto.start_date,
            dto.end_date,
            [user.id],
        )

        # Фильтруем реакции только для данного пользователя
        user_reactions = [r for r in reactions if r.user_id == user.id]

        return {"messages": messages, "reactions": user_reactions}

    def _generate_user_breaks_detail(self, data: dict, user: User) -> str:
        """Генерирует детализацию перерывов для одного пользователя."""
        messages = data["messages"]
        reactions = data["reactions"]

        # Если нет активности - не показываем пользователя
        if not messages and not reactions:
            return ""

        breaks = BreakAnalysisService.calculate_breaks(
            messages,
            reactions,
            min_break_minutes=chat.breaks_time,
        )

        # Показываем пользователя только если есть перерывы
        if not breaks:
            return ""

        user_report = f"<b>👤 @{user.username}</b>\n<b>⏸️ Перерывы:</b>\n"
        user_report += "\n".join(breaks)

        return user_report

    @staticmethod
    def _has_time_settings(chat) -> bool:
        return (
            chat.start_time is not None
            and chat.end_time is not None
            and chat.tolerance is not None
            and chat.breaks_time is not None
        )
