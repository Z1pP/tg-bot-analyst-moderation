"""Тесты GetChatReportUseCase: пустой чат, один пользователь, ошибки и успешный сценарий (с моками)."""

from datetime import datetime, time, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from dto.report import ChatReportDTO, ReportResultDTO
from models import ChatSession
from usecases.report.chat.get_chat_report import GetChatReportUseCase


def test_has_time_settings_true() -> None:
    """_has_time_settings возвращает True при всех полях заданных."""
    chat = MagicMock()
    chat.start_time = time(9, 0)
    chat.end_time = time(18, 0)
    chat.tolerance = 30
    chat.breaks_time = 15
    assert GetChatReportUseCase._has_time_settings(chat) is True


def test_has_time_settings_false() -> None:
    """_has_time_settings возвращает False при отсутствии одного из полей."""
    chat = MagicMock()
    chat.start_time = time(9, 0)
    chat.end_time = None
    chat.tolerance = 30
    chat.breaks_time = 15
    assert GetChatReportUseCase._has_time_settings(chat) is False


@pytest.fixture
def chat_report_dto() -> ChatReportDTO:
    """DTO отчёта по чату."""
    return ChatReportDTO(
        chat_id=1,
        admin_tg_id="admin_1",
        selected_period="За сегодня",
        start_date=None,
        end_date=None,
        chat_tgid="-100",
    )


@pytest.fixture
def usecase() -> GetChatReportUseCase:
    """Use case с замоканными зависимостями."""
    return GetChatReportUseCase(
        chat_repository=AsyncMock(),
        user_repository=AsyncMock(),
        message_repository=AsyncMock(),
        reaction_repository=AsyncMock(),
        msg_reply_repository=AsyncMock(),
        punishment_repository=AsyncMock(),
        bot_permission_service=None,
        admin_action_log_service=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_execute_chat_not_found_returns_error_dto(
    usecase: GetChatReportUseCase,
    chat_report_dto: ChatReportDTO,
) -> None:
    """Чат не найден — возвращается DTO с error_message, даты из периода."""
    usecase._chat_repository.get_chat_by_id = AsyncMock(return_value=None)

    result = await usecase.execute(chat_report_dto)

    assert isinstance(result, ReportResultDTO)
    assert result.error_message is not None
    assert (
        "чат" in result.error_message.lower()
        or "не найден" in result.error_message.lower()
        or "удалён" in result.error_message.lower()
    )
    assert result.chat_title == ""
    assert result.start_date is not None
    assert result.end_date is not None
    assert result.users_stats == []


@pytest.mark.asyncio
async def test_execute_no_time_settings_returns_error_dto(
    usecase: GetChatReportUseCase,
    chat_report_dto: ChatReportDTO,
) -> None:
    """Чат без настроек времени — error_message о необходимости настроек."""
    chat = ChatSession(chat_id="-100", title="Test Chat")
    chat.id = 1
    chat.settings = None  # без настроек start_time/end_time будут None
    usecase._chat_repository.get_chat_by_id = AsyncMock(return_value=chat)

    result = await usecase.execute(chat_report_dto)

    assert result.error_message is not None
    assert (
        "настройк" in result.error_message.lower()
        or "врем" in result.error_message.lower()
    )
    assert result.chat_title == "Test Chat"
    assert result.users_stats == []


@pytest.mark.asyncio
async def test_execute_no_tracked_users_returns_error_dto(
    usecase: GetChatReportUseCase,
    chat_report_dto: ChatReportDTO,
) -> None:
    """Нет отслеживаемых пользователей — error_message, пустая статистика."""
    chat = MagicMock()
    chat.id = 1
    chat.chat_id = "-100"
    chat.title = "Test Chat"
    chat.start_time = time(9, 0)
    chat.end_time = time(18, 0)
    chat.tolerance = 30
    chat.breaks_time = 15
    usecase._chat_repository.get_chat_by_id = AsyncMock(return_value=chat)
    usecase._user_repository.get_tracked_users_for_admin = AsyncMock(return_value=[])

    result = await usecase.execute(chat_report_dto)

    assert result.error_message is not None
    assert result.users_stats == []
    assert result.chat_title == "Test Chat"


@pytest.mark.asyncio
async def test_execute_success_returns_report_result(
    usecase: GetChatReportUseCase,
    chat_report_dto: ChatReportDTO,
) -> None:
    """Успешный сценарий: чат с настройками, один отслеживаемый пользователь, одно сообщение — возвращается отчёт без ошибки."""
    chat = MagicMock()
    chat.id = 1
    chat.chat_id = "-100"
    chat.title = "Test Chat"
    chat.start_time = time(9, 0)
    chat.end_time = time(18, 0)
    chat.tolerance = 30
    chat.breaks_time = 15

    tracked_user = MagicMock()
    tracked_user.id = 1
    tracked_user.tg_id = "u1"
    tracked_user.username = "tracked_user"
    msg = MagicMock()
    msg.user_id = 1
    msg.created_at = datetime.now(timezone.utc)
    msg.user = MagicMock(username="tracked_user")

    usecase._chat_repository.get_chat_by_id = AsyncMock(return_value=chat)
    usecase._user_repository.get_tracked_users_for_admin = AsyncMock(
        return_value=[tracked_user]
    )
    usecase._message_repository.get_messages_by_chat_id_and_period = AsyncMock(
        return_value=[msg]
    )
    usecase._reaction_repository.get_reactions_by_chat_and_period = AsyncMock(
        return_value=[]
    )
    usecase._msg_reply_repository.get_replies_by_chat_id_and_period = AsyncMock(
        return_value=[]
    )
    usecase._punishment_repository.get_punishment_counts_by_moderators = AsyncMock(
        return_value={1: {"warns": 0, "bans": 0}}
    )

    # Фиксируем даты, чтобы WorkTimeService.calculate_work_hours получал реальные datetime
    start_dt = datetime(2025, 2, 22, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2025, 2, 22, 18, 0, 0, tzinfo=timezone.utc)
    with patch(
        "usecases.report.chat.get_chat_report.TimePeriod.to_datetime",
        return_value=(start_dt, end_dt),
    ):
        with patch(
            "usecases.report.chat.get_chat_report.WorkTimeService.adjust_dates_to_work_hours",
            return_value=(start_dt, end_dt),
        ):
            result = await usecase.execute(chat_report_dto)

    assert isinstance(result, ReportResultDTO)
    assert result.error_message is None
    assert result.chat_title == "Test Chat"
    assert result.start_date is not None
    assert result.end_date is not None
    assert len(result.users_stats) == 1
    assert result.users_stats[0].user_id == 1
    assert result.users_stats[0].username == "tracked_user"
    usecase._admin_action_log_service.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_execute_calculate_users_stats_with_multiple_users_and_reactions(
    usecase: GetChatReportUseCase,
    chat_report_dto: ChatReportDTO,
) -> None:
    """_calculate_users_stats с несколькими пользователями и реакциями — все попадают в users_stats."""
    chat = MagicMock()
    chat.id = 1
    chat.chat_id = "-100"
    chat.title = "Chat"
    chat.start_time = time(9, 0)
    chat.end_time = time(18, 0)
    chat.tolerance = 30
    chat.breaks_time = 15

    u1, u2 = MagicMock(), MagicMock()
    u1.id, u1.tg_id, u1.username = 1, "u1", "user1"
    u2.id, u2.tg_id, u2.username = 2, "u2", "user2"

    msg1 = MagicMock()
    msg1.user_id = 1
    msg1.created_at = datetime(2025, 2, 22, 10, 0, tzinfo=timezone.utc)
    msg1.user = u1
    msg2 = MagicMock()
    msg2.user_id = 2
    msg2.created_at = datetime(2025, 2, 22, 11, 0, tzinfo=timezone.utc)
    msg2.user = u2
    react = MagicMock()
    react.user_id = 2
    react.created_at = datetime(2025, 2, 22, 12, 0, tzinfo=timezone.utc)
    react.user = u2

    usecase._chat_repository.get_chat_by_id = AsyncMock(return_value=chat)
    usecase._user_repository.get_tracked_users_for_admin = AsyncMock(
        return_value=[u1, u2]
    )
    usecase._message_repository.get_messages_by_chat_id_and_period = AsyncMock(
        return_value=[msg1, msg2]
    )
    usecase._reaction_repository.get_reactions_by_chat_and_period = AsyncMock(
        return_value=[react]
    )
    usecase._msg_reply_repository.get_replies_by_chat_id_and_period = AsyncMock(
        return_value=[]
    )
    usecase._punishment_repository.get_punishment_counts_by_moderators = AsyncMock(
        return_value={1: {"warns": 0, "bans": 0}, 2: {"warns": 0, "bans": 0}}
    )

    start_dt = datetime(2025, 2, 22, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2025, 2, 22, 18, 0, 0, tzinfo=timezone.utc)
    with patch(
        "usecases.report.chat.get_chat_report.TimePeriod.to_datetime",
        return_value=(start_dt, end_dt),
    ):
        with patch(
            "usecases.report.chat.get_chat_report.WorkTimeService.adjust_dates_to_work_hours",
            return_value=(start_dt, end_dt),
        ):
            result = await usecase.execute(chat_report_dto)

    assert result.error_message is None
    assert len(result.users_stats) == 2
    user_ids = {s.user_id for s in result.users_stats}
    assert user_ids == {1, 2}
