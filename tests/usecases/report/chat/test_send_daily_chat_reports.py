"""Тесты SendDailyChatReportsUseCase: пустой чат, нет архива, ошибки и успешная рассылка (с моками)."""

from datetime import datetime, time, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from models import ChatSession
from usecases.report.chat.send_daily_chat_reports import SendDailyChatReportsUseCase


@pytest.fixture
def usecase() -> SendDailyChatReportsUseCase:
    """Use case с замоканными зависимостями."""
    return SendDailyChatReportsUseCase(
        chat_repository=AsyncMock(),
        user_repository=AsyncMock(),
        message_repository=AsyncMock(),
        msg_reply_repository=AsyncMock(),
        reaction_repository=AsyncMock(),
        bot_message_service=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_execute_chat_not_found_returns_early(
    usecase: SendDailyChatReportsUseCase,
) -> None:
    """Чат не найден — выполнение завершается без отправки."""
    usecase._chat_repository.get_chat_by_id = AsyncMock(return_value=None)

    await usecase.execute(chat_id=999, period="За сегодня")

    usecase._bot_message_service.send_chat_message.assert_not_called()


@pytest.mark.asyncio
async def test_execute_no_archive_chat_returns_early(
    usecase: SendDailyChatReportsUseCase,
) -> None:
    """Чат без архивного чата — выполнение завершается без отправки."""
    chat = ChatSession(chat_id="-100", title="Test", archive_chat_id=None)
    chat.id = 1
    usecase._chat_repository.get_chat_by_id = AsyncMock(return_value=chat)

    await usecase.execute(chat_id=1, period="За сегодня")

    usecase._bot_message_service.send_chat_message.assert_not_called()


@pytest.mark.asyncio
async def test_execute_no_time_settings_notifies_admins(
    usecase: SendDailyChatReportsUseCase,
) -> None:
    """Нет настроек времени — уведомление админам, отправки в архив нет."""
    from models import User

    chat = ChatSession(chat_id="-100", title="Test", archive_chat_id="-200")
    chat.id = 1
    chat.settings = None  # без настроек _has_time_settings вернёт False
    admin = User(id=1, tg_id="adm_1", username="admin")
    usecase._chat_repository.get_chat_by_id = AsyncMock(return_value=chat)
    usecase._user_repository.get_admins_for_chat = AsyncMock(return_value=[admin])

    await usecase.execute(chat_id=1, period="За сегодня")

    usecase._bot_message_service.send_private_message.assert_called()
    usecase._bot_message_service.send_chat_message.assert_not_called()


@pytest.mark.asyncio
async def test_execute_success_sends_report_to_archive(
    usecase: SendDailyChatReportsUseCase,
) -> None:
    """Успешный сценарий: чат с архивом и настройками, есть отслеживаемые пользователи и данные — отправка отчёта в архивный чат."""
    chat = MagicMock()
    chat.id = 1
    chat.chat_id = "-100"
    chat.title = "Work Chat"
    chat.archive_chat_id = "-200"
    chat.start_time = time(9, 0)
    chat.end_time = time(18, 0)
    chat.tolerance = 30
    chat.breaks_time = 15

    admin = MagicMock()
    admin.tg_id = "adm_1"
    tracked_user = MagicMock()
    tracked_user.id = 1
    tracked_user.username = "tracked_user"

    msg = MagicMock()
    msg.user_id = 1
    msg.created_at = datetime.now(timezone.utc)
    msg.user = MagicMock(username="tracked_user")

    usecase._chat_repository.get_chat_by_id = AsyncMock(return_value=chat)
    usecase._user_repository.get_admins_for_chat = AsyncMock(return_value=[admin])
    usecase._user_repository.get_tracked_users_for_admin = AsyncMock(
        return_value=[tracked_user]
    )
    usecase._message_repository.get_messages_by_chat_id_and_period = AsyncMock(
        return_value=[msg]
    )
    usecase._msg_reply_repository.get_replies_by_chat_id_and_period = AsyncMock(
        return_value=[]
    )
    usecase._reaction_repository.get_reactions_by_chat_and_period = AsyncMock(
        return_value=[]
    )

    # Фиксируем даты, чтобы WorkTimeService.calculate_work_hours получал реальные datetime
    start_dt = datetime(2025, 2, 22, 0, 0, 0, tzinfo=timezone.utc)
    end_dt = datetime(2025, 2, 22, 18, 0, 0, tzinfo=timezone.utc)
    with patch(
        "usecases.report.chat.send_daily_chat_reports.TimePeriod.to_datetime",
        return_value=(start_dt, end_dt),
    ):
        with patch(
            "usecases.report.chat.send_daily_chat_reports.WorkTimeService.adjust_dates_to_work_hours",
            return_value=(start_dt, end_dt),
        ):
            await usecase.execute(chat_id=1, period="За сегодня")

    usecase._bot_message_service.send_chat_message.assert_called_once()
    call_kw = usecase._bot_message_service.send_chat_message.call_args.kwargs
    assert call_kw["chat_tgid"] == "-200"
    assert "Отчёт" in call_kw["text"] or "отчёт" in call_kw["text"]
    assert "Work Chat" in call_kw["text"]
