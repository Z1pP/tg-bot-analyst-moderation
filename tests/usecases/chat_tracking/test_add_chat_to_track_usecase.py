"""Тесты для AddChatToTrackUseCase: успех, админ не найден, чат не создан, нет прав, уже отслеживается, ошибка добавления, BotBaseException."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from exceptions import BotBaseException
from usecases.chat_tracking.add_chat_to_track_usecase import (
    AddChatToTrackUseCase,
)


@pytest.fixture
def usecase() -> AddChatToTrackUseCase:
    return AddChatToTrackUseCase(
        chat_tracking_repository=AsyncMock(),
        admin_action_log_service=AsyncMock(),
        user_service=AsyncMock(),
        chat_service=AsyncMock(),
        bot_permission_service=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_execute_admin_not_found_returns_error(
    usecase: AddChatToTrackUseCase,
) -> None:
    """Если администратор не найден — success=False, error_message задан."""
    usecase._user_service.get_user = AsyncMock(return_value=None)

    result = await usecase.execute(
        admin_tg_id="1",
        chat_tg_id="-100",
        chat_title="Chat",
    )

    assert result.success is False
    assert result.error_message == "Администратор не найден"
    usecase._chat_service.get_or_create.assert_not_called()


@pytest.mark.asyncio
async def test_execute_chat_not_created_returns_error(
    usecase: AddChatToTrackUseCase,
) -> None:
    """Если get_or_create чата вернул None — error_message «Не удалось получить чат»."""
    admin = SimpleNamespace(id=1, tg_id="1", username="admin")
    usecase._user_service.get_user = AsyncMock(return_value=admin)
    usecase._chat_service.get_or_create = AsyncMock(return_value=None)

    result = await usecase.execute(
        admin_tg_id="1",
        chat_tg_id="-100",
        chat_title="Chat",
    )

    assert result.success is False
    assert result.error_message == "Не удалось получить чат"


@pytest.mark.asyncio
async def test_execute_no_permissions_returns_without_success(
    usecase: AddChatToTrackUseCase,
) -> None:
    """Если у бота нет прав — success=False, access не создаётся."""
    admin = SimpleNamespace(id=1, tg_id="1", username="admin")
    chat = SimpleNamespace(id=1, chat_id="-100", title="Chat")
    usecase._user_service.get_user = AsyncMock(return_value=admin)
    usecase._chat_service.get_or_create = AsyncMock(return_value=chat)
    usecase._bot_permission_service.check_archive_permissions = AsyncMock(
        return_value=SimpleNamespace(
            has_all_permissions=False,
            missing_permissions=["can_delete_messages"],
        )
    )

    result = await usecase.execute(
        admin_tg_id="1",
        chat_tg_id="-100",
        chat_title="Chat",
    )

    assert result.success is False
    assert result.permissions_check is not None
    usecase._chat_tracking_repository.get_access.assert_not_called()


@pytest.mark.asyncio
async def test_execute_already_tracked_returns_success(
    usecase: AddChatToTrackUseCase,
) -> None:
    """Если чат уже отслеживается — success=True, is_already_tracked=True."""
    admin = SimpleNamespace(id=1, tg_id="1", username="admin")
    chat = SimpleNamespace(id=1, chat_id="-100", title="Chat")
    existing_access = SimpleNamespace(admin_id=1, chat_id=1)
    usecase._user_service.get_user = AsyncMock(return_value=admin)
    usecase._chat_service.get_or_create = AsyncMock(return_value=chat)
    usecase._bot_permission_service.check_archive_permissions = AsyncMock(
        return_value=SimpleNamespace(has_all_permissions=True)
    )
    usecase._chat_tracking_repository.get_access = AsyncMock(
        return_value=existing_access
    )

    result = await usecase.execute(
        admin_tg_id="1",
        chat_tg_id="-100",
        chat_title="Chat",
    )

    assert result.success is True
    assert result.is_already_tracked is True
    assert result.access == existing_access
    usecase._chat_tracking_repository.add_chat_to_tracking.assert_not_called()


@pytest.mark.asyncio
async def test_execute_add_chat_returns_none_returns_error(
    usecase: AddChatToTrackUseCase,
) -> None:
    """Если add_chat_to_tracking вернул None — error_message задан."""
    admin = SimpleNamespace(id=1, tg_id="1", username="admin")
    chat = SimpleNamespace(id=1, chat_id="-100", title="Chat")
    usecase._user_service.get_user = AsyncMock(return_value=admin)
    usecase._chat_service.get_or_create = AsyncMock(return_value=chat)
    usecase._bot_permission_service.check_archive_permissions = AsyncMock(
        return_value=SimpleNamespace(has_all_permissions=True)
    )
    usecase._chat_tracking_repository.get_access = AsyncMock(return_value=None)
    usecase._chat_tracking_repository.add_chat_to_tracking = AsyncMock(
        return_value=None
    )

    result = await usecase.execute(
        admin_tg_id="1",
        chat_tg_id="-100",
        chat_title="Chat",
    )

    assert result.success is False
    assert result.error_message == "Не удалось добавить чат в отслеживание"


@pytest.mark.asyncio
async def test_execute_success_logs_and_returns_result(
    usecase: AddChatToTrackUseCase,
) -> None:
    """Успешное добавление: логирование и success=True."""
    admin = SimpleNamespace(id=1, tg_id="1", username="admin")
    chat = SimpleNamespace(id=1, chat_id="-100", title="Chat")
    access = SimpleNamespace(admin_id=1, chat_id=1)
    usecase._user_service.get_user = AsyncMock(return_value=admin)
    usecase._chat_service.get_or_create = AsyncMock(return_value=chat)
    usecase._bot_permission_service.check_archive_permissions = AsyncMock(
        return_value=SimpleNamespace(has_all_permissions=True)
    )
    usecase._chat_tracking_repository.get_access = AsyncMock(return_value=None)
    usecase._chat_tracking_repository.add_chat_to_tracking = AsyncMock(
        return_value=access
    )

    result = await usecase.execute(
        admin_tg_id="1",
        chat_tg_id="-100",
        chat_title="Chat",
        admin_username="admin",
    )

    assert result.success is True
    assert result.access == access
    assert result.is_already_tracked is False
    usecase._admin_action_log_service.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_execute_bot_base_exception_returns_error_message(
    usecase: AddChatToTrackUseCase,
) -> None:
    """При BotBaseException результат содержит error_message."""
    usecase._user_service.get_user = AsyncMock(
        side_effect=BotBaseException("Ошибка БД")
    )

    result = await usecase.execute(
        admin_tg_id="1",
        chat_tg_id="-100",
        chat_title="Chat",
    )

    assert result.success is False
    assert result.error_message == "Ошибка БД"
