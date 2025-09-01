import logging
from typing import List

from dto.report import AllUsersReportDTO
from models import User
from services.break_analysis_service import BreakAnalysisService

from .base import BaseReportUseCase

logger = logging.getLogger(__name__)


class GetAllUsersBreaksDetailReportUseCase(BaseReportUseCase):
    async def execute(self, dto: AllUsersReportDTO) -> List[str]:
        """Генерирует детализированный отчет по перерывам для всех пользователей."""
        users = await self._user_repository.get_tracked_users_for_admin(
            admin_tg_id=dto.user_tg_id,
        )

        if not users:
            return ["⚠️ Список пользователей пуст, добавьте пользователя!"]

        period = self._format_selected_period(
            start_date=dto.start_date,
            end_date=dto.end_date,
        )
        
        report_title = f"<b>📊 Детализация перерывов по датам за {period}</b>"
        
        reports = []
        for user in users:
            user_data = await self._get_user_data(user, dto)
            if not user_data["messages"] and not user_data["reactions"]:
                continue

            user_report = self._generate_user_breaks_detail(user_data, user)
            if user_report:
                reports.append(user_report)

        if not reports:
            return [f"{report_title}\n\n⚠️ Нет данных для детализации за указанный период"]

        full_report = "\n\n".join([report_title] + reports)
        return self._split_report(full_report)

    async def _get_user_data(self, user: User, dto: AllUsersReportDTO) -> dict:
        """Получает данные пользователя за период."""
        messages = await self._get_processed_items(
            self._message_repository.get_messages_by_period_date,
            user.id,
            dto.start_date,
            dto.end_date,
        )

        reactions = await self._get_processed_items(
            self._reaction_repository.get_reactions_by_user_and_period,
            user.id,
            dto.start_date,
            dto.end_date,
        )

        return {"messages": messages, "reactions": reactions}

    def _generate_user_breaks_detail(self, data: dict, user: User) -> str:
        """Генерирует детализацию перерывов для одного пользователя."""
        messages = data["messages"]
        reactions = data["reactions"]

        if not messages and not reactions:
            return ""

        breaks = BreakAnalysisService.calculate_breaks(messages, reactions)
        
        if not breaks:
            return f"<b>👤 @{user.username}</b>\n⏸️ Перерывы: отсутствуют"

        user_report = f"<b>👤 @{user.username}</b>\n<b>⏸️ Перерывы:</b>\n"
        user_report += "\n".join(breaks)
        
        return user_report