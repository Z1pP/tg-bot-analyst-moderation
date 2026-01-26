import logging
from datetime import datetime

from dto.report import (
    BreaksDetailReportDTO,
    BreaksDetailUserDTO,
    SingleUserReportDTO,
)
from exceptions.user import UserNotFoundException
from models import User
from services.break_analysis_service import BreakAnalysisService

from .base import BaseReportUseCase

logger = logging.getLogger(__name__)


class GetBreaksDetailReportUseCase(BaseReportUseCase):
    async def execute(self, report_dto: SingleUserReportDTO) -> BreaksDetailReportDTO:
        """Генерирует детализированный отчет по перерывам пользователя."""
        user = await self._get_user(user_id=report_dto.user_id)
        user_data = await self._get_user_data(user=user, dto=report_dto)

        report = self._generate_breaks_detail_report(
            user_data, user, report_dto.start_date, report_dto.end_date
        )

        return report

    async def _get_user(self, user_id: int) -> User:
        """Получает пользователя по user_id."""
        user = await self._user_repository.get_user_by_id(user_id=user_id)
        if not user:
            logger.error(f"Пользователь с ID={user_id} не найден")
            raise UserNotFoundException()
        return user

    async def _get_user_data(self, user: User, dto: SingleUserReportDTO) -> dict:
        """Получает данные пользователя за период."""
        # Проверяем наличие отслеживаемых чатов
        tracked_chats = await self._chat_repository.get_tracked_chats_for_admin(
            dto.admin_tg_id
        )
        if not tracked_chats:
            return {"no_chats": True}

        tracked_chat_ids = [chat.id for chat in tracked_chats]

        messages = await self._get_processed_items_by_user_in_chats(
            repository_method=self._message_repository.get_messages_by_period_date_and_chats,
            user_id=user.id,
            start_date=dto.start_date,
            end_date=dto.end_date,
            chat_ids=tracked_chat_ids,
        )

        reactions = await self._get_processed_items_by_user_in_chats(
            repository_method=self._reaction_repository.get_reactions_by_user_and_period_and_chats,
            user_id=user.id,
            start_date=dto.start_date,
            end_date=dto.end_date,
            chat_ids=tracked_chat_ids,
        )

        return {"messages": messages, "reactions": reactions}

    def _generate_breaks_detail_report(
        self,
        data: dict,
        user: User,
        start_date: datetime,
        end_date: datetime,
    ) -> BreaksDetailReportDTO:
        """Генерирует детализированный отчет по перерывам."""
        period = self._format_selected_period(start_date, end_date)

        # Проверяем наличие отслеживаемых чатов
        if data.get("no_chats"):
            return BreaksDetailReportDTO(
                period=period,
                users=[],
                error_message="⚠️ Необходимо добавить чат в отслеживание.",
            )

        messages = data.get("messages", [])
        reactions = data.get("reactions", [])

        if not messages and not reactions:
            return BreaksDetailReportDTO(
                period=period,
                users=[],
                error_message="⚠️ Нет данных за указанный период.",
            )

        breaks_detail = BreakAnalysisService.calculate_breaks_structured(
            messages, reactions
        )

        user_detail = BreaksDetailUserDTO(
            username=user.username,
            has_activity=bool(messages or reactions),
            days=breaks_detail,
        )

        return BreaksDetailReportDTO(period=period, users=[user_detail])
