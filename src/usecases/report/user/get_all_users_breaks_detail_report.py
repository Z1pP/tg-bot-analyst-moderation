import logging

from dto.report import (
    AllUsersReportDTO,
    BreaksDetailReportDTO,
    BreaksDetailUserDTO,
)
from models import User
from services.break_analysis_service import BreakAnalysisService

from .base import BaseReportUseCase

logger = logging.getLogger(__name__)


class GetAllUsersBreaksDetailReportUseCase(BaseReportUseCase):
    async def execute(self, dto: AllUsersReportDTO) -> BreaksDetailReportDTO:
        """Генерирует детализированный отчет по перерывам для всех пользователей."""
        users = await self._user_repository.get_tracked_users_for_admin(
            admin_tg_id=dto.user_tg_id,
        )

        if not users:
            return BreaksDetailReportDTO(
                period="",
                users=[],
                error_message="⚠️ Список пользователей пуст, добавьте пользователя!",
            )

        period = self._format_selected_period(
            start_date=dto.start_date,
            end_date=dto.end_date,
        )

        reports = []
        for user in users:
            user_data = await self._get_user_data(user, dto)
            user_report = self._generate_user_breaks_detail(user_data, user, period)
            if user_report:
                reports.append(user_report)

        if not reports:
            return BreaksDetailReportDTO(
                period=period,
                users=[],
                error_message="⚠️ Нет данных для детализации за указанный период",
            )

        return BreaksDetailReportDTO(period=period, users=reports)

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

    def _generate_user_breaks_detail(
        self, data: dict, user: User, period: str
    ) -> BreaksDetailUserDTO:
        """Генерирует детализацию перерывов для одного пользователя."""
        messages = data["messages"]
        reactions = data["reactions"]

        if not messages and not reactions:
            return BreaksDetailUserDTO(
                username=user.username,
                has_activity=False,
                days=[],
            )

        breaks = BreakAnalysisService.calculate_breaks_structured(messages, reactions)

        return BreaksDetailUserDTO(
            username=user.username,
            has_activity=True,
            days=breaks,
        )
