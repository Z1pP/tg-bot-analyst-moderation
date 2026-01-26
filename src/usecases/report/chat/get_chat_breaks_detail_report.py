import logging

from constants.dialogs import ReportDialogs
from dto.report import BreaksDetailReportDTO, BreaksDetailUserDTO, ChatReportDTO
from models import ChatSession, User
from services.break_analysis_service import BreakAnalysisService
from utils.collection_utils import group_by

from ..base import ChatReportUseCase

logger = logging.getLogger(__name__)


class GetChatBreaksDetailReportUseCase(ChatReportUseCase):
    async def execute(self, dto: ChatReportDTO) -> BreaksDetailReportDTO:
        """Генерирует детализированный отчет по перерывам для чата."""
        # Получаем отслеживаемых пользователей
        users = await self._user_repository.get_tracked_users_for_admin(
            admin_tg_id=dto.admin_tg_id,
        )

        if not users:
            return BreaksDetailReportDTO(
                period="",
                users=[],
                error_message="⚠️ Список пользователей пуст, добавьте пользователя!",
            )

        # Получаем информацию о чате
        chat = await self._chat_repository.get_chat_by_id(dto.chat_id)
        if not chat:
            return BreaksDetailReportDTO(
                period="",
                users=[],
                error_message="⚠️ Чат не найден!",
            )

        if not self._has_time_settings(chat=chat):
            return BreaksDetailReportDTO(
                period="",
                users=[],
                error_message=ReportDialogs.CHAT_REPORT_SETTINGS_REQUIRED,
            )

        period = self._format_selected_period(
            start_date=dto.start_date,
            end_date=dto.end_date,
        )
        user_ids = [user.id for user in users]
        users_data = await self._get_all_users_data_for_chat(
            user_ids=user_ids,
            dto=dto,
        )

        reports = []
        for user in users:
            user_data = users_data.get(user.id, {"messages": [], "reactions": []})
            user_report = self._generate_user_breaks_detail(
                data=user_data,
                user=user,
                chat=chat,
                period=period,
            )

            if user_report:
                reports.append(user_report)

        if not reports:
            return BreaksDetailReportDTO(
                period=period,
                users=[],
                error_message="⚠️ Нет данных для детализации за указанный период",
            )

        return BreaksDetailReportDTO(period=period, users=reports)

    async def _get_all_users_data_for_chat(
        self, user_ids: list[int], dto: ChatReportDTO
    ) -> dict:
        """Получает данные пользователей за период в конкретном чате."""
        messages = await self._get_processed_items_by_chat_with_users(
            self._message_repository.get_messages_by_chat_id_and_period,
            dto.chat_id,
            dto.start_date,
            dto.end_date,
            user_ids,
        )

        reactions = await self._get_processed_items_by_chat_with_users(
            self._reaction_repository.get_reactions_by_chat_and_period,
            dto.chat_id,
            dto.start_date,
            dto.end_date,
            user_ids,
        )

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
        self,
        data: dict,
        user: User,
        chat: ChatSession,
        period: str,
    ) -> BreaksDetailUserDTO:
        """Генерирует детализацию перерывов для одного пользователя."""
        messages = data["messages"]
        reactions = data["reactions"]

        # Если нет активности - показываем отсутствие перерывов
        if not messages and not reactions:
            return BreaksDetailUserDTO(
                username=user.username,
                has_activity=False,
                days=[],
            )

        breaks = BreakAnalysisService.calculate_breaks_structured(
            messages,
            reactions,
            min_break_minutes=chat.breaks_time,
        )

        return BreaksDetailUserDTO(
            username=user.username,
            has_activity=True,
            days=breaks,
        )

    @staticmethod
    def _has_time_settings(chat) -> bool:
        return (
            chat.start_time is not None
            and chat.end_time is not None
            and chat.tolerance is not None
            and chat.breaks_time is not None
        )
