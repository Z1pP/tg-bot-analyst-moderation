"""Тесты для RemoveChatFromTrackingUseCase."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from usecases.chat_tracking.remove_chat_from_tracking import (
    RemoveChatFromTrackingResult,
    RemoveChatFromTrackingUseCase,
)


@pytest.fixture
def use_case() -> RemoveChatFromTrackingUseCase:
    return RemoveChatFromTrackingUseCase(
        chat_tracking_repository=AsyncMock(),
        admin_action_log_service=AsyncMock(),
        user_service=AsyncMock(),
        chat_service=AsyncMock(),
        bot_permission_service=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_remove_chat_from_tracking_admin_not_found(
    use_case: RemoveChatFromTrackingUseCase,
) -> None:
    """Если администратор не найден, возвращается result с error_message и success=False."""
    use_case._user_service.get_user = AsyncMock(return_value=None)

    result = await use_case.execute(
        admin_tg_id="unknown",
        chat_tg_id="-100",
        chat_title="Чат",
    )

    assert isinstance(result, RemoveChatFromTrackingResult)
    assert result.success is False
    assert result.admin is None
    assert result.error_message == "Администратор не найден"
    use_case._chat_service.get_chat.assert_not_called()


@pytest.mark.asyncio
async def test_remove_chat_from_tracking_chat_not_found(
    use_case: RemoveChatFromTrackingUseCase,
) -> None:
    """Если чат не найден, возвращается result с error_message."""
    admin = SimpleNamespace(id=1, tg_id="123", username="admin")
    use_case._user_service.get_user = AsyncMock(return_value=admin)
    use_case._chat_service.get_chat = AsyncMock(return_value=None)

    result = await use_case.execute(
        admin_tg_id="123",
        chat_tg_id="-100",
        chat_title="Чат",
    )

    assert result.success is False
    assert result.admin == admin
    assert result.chat is None
    assert result.error_message == "Чат не найден"


@pytest.mark.asyncio
async def test_remove_chat_from_tracking_chat_not_tracked(
    use_case: RemoveChatFromTrackingUseCase,
) -> None:
    """Если чат не отслеживается, возвращается is_chat_not_tracked=True и success=False."""
    admin = SimpleNamespace(id=1, tg_id="123", username="admin")
    chat = SimpleNamespace(id=10, chat_id="-100", title="Чат")
    perm_ok = SimpleNamespace(has_all_permissions=True)
    use_case._user_service.get_user = AsyncMock(return_value=admin)
    use_case._chat_service.get_chat = AsyncMock(return_value=chat)
    use_case._bot_permission_service.check_archive_permissions = AsyncMock(
        return_value=perm_ok
    )
    use_case._chat_tracking_repository.get_access = AsyncMock(return_value=None)

    result = await use_case.execute(
        admin_tg_id="123",
        chat_tg_id="-100",
        chat_title="Чат",
    )

    assert result.success is False
    assert result.is_chat_not_tracked is True
    assert result.admin == admin
    assert result.chat == chat
    use_case._chat_tracking_repository.remove_chat_from_tracking.assert_not_called()
