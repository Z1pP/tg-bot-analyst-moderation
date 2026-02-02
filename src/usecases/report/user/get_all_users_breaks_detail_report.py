import logging

from dto.report import AllUsersReportDTO, BreaksDetailReportDTO, BreaksDetailUserDTO
from models import User
from services.break_analysis_service import BreakAnalysisService
from utils.collection_utils import group_by

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

        user_ids = [user.id for user in users]
        users_data = await self._get_all_users_data(user_ids, dto)

        reports = []
        for user in users:
            user_data = users_data.get(user.id, {"messages": [], "reactions": []})
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

    async def _get_all_users_data(
        self, user_ids: list[int], dto: AllUsersReportDTO
    ) -> dict:
        """Получает данные пользователей за период одной выборкой."""
        messages = await self._message_repository.get_messages_by_period_date_for_users(
            user_ids=user_ids,
            start_date=dto.start_date,
            end_date=dto.end_date,
        )
        reactions = (
            await self._reaction_repository.get_reactions_by_user_and_period_for_users(
                user_ids=user_ids,
                start_date=dto.start_date,
                end_date=dto.end_date,
            )
        )

        messages = self._process_items(messages)
        reactions = self._process_items(reactions)

        messages_by_user = group_by(messages, lambda m: m.user_id)
        reactions_by_user = group_by(reactions, lambda r: r.user_id)

        return {
            user_id: {
                "messages": messages_by_user.get(user_id, []),
                "reactions": reactions_by_user.get(user_id, []),
            }
            for user_id in user_ids
        }

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
