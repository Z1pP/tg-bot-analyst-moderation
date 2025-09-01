import logging
from datetime import datetime
from typing import List

from dto.report import SingleUserReportDTO
from exceptions.user import UserNotFoundException
from models import User
from services.break_analysis_service import BreakAnalysisService

from .base import BaseReportUseCase

logger = logging.getLogger(__name__)


class GetBreaksDetailReportUseCase(BaseReportUseCase):

    async def execute(self, report_dto: SingleUserReportDTO) -> List[str]:
        """Генерирует детализированный отчет по перерывам пользователя."""
        user = await self._get_user(user_id=report_dto.user_id)
        user_data = await self._get_user_data(user=user, dto=report_dto)

        full_report = self._generate_breaks_detail_report(
            user_data, user, report_dto.start_date, report_dto.end_date
        )

        return self._split_report(full_report)

    async def _get_user(self, user_id: int) -> User:
        """Получает пользователя по user_id."""
        user = await self._user_repository.get_user_by_id(user_id=user_id)
        if not user:
            logger.error(f"Пользователь с ID={user_id} не найден")
            raise UserNotFoundException()
        return user

    async def _get_user_data(self, user: User, dto: SingleUserReportDTO) -> dict:
        """Получает данные пользователя за период."""
        messages = await self._get_processed_items(
            repository_method=self._message_repository.get_messages_by_period_date,
            user_id=user.id,
            start_date=dto.start_date,
            end_date=dto.end_date,
        )

        reactions = await self._get_processed_items(
            repository_method=self._reaction_repository.get_reactions_by_user_and_period,
            user_id=user.id,
            start_date=dto.start_date,
            end_date=dto.end_date,
        )

        return {"messages": messages, "reactions": reactions}

    def _generate_breaks_detail_report(
        self,
        data: dict,
        user: User,
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """Генерирует детализированный отчет по перерывам."""
        messages = data.get("messages", [])
        reactions = data.get("reactions", [])

        period = self._format_selected_period(start_date, end_date)
        header = f"<b>📈 Детализация перерывов: @{user.username} за {period}</b>\n\n"

        if not messages and not reactions:
            return header + "⚠️ Нет данных за указанный период."

        breaks_detail = BreakAnalysisService.calculate_breaks(messages, reactions)

        if not breaks_detail:
            return header + "<b>⏸️ Перерывы отсутствуют</b>"

        return header + "\n".join(breaks_detail)
