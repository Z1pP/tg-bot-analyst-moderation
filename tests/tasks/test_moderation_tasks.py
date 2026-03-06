"""Тесты moderation_tasks: kick_unverified_member_task, delete_message_from_chat."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tasks.moderation_tasks import (
    delete_message_from_chat,
    kick_unverified_member_task,
)


@pytest.fixture
def mock_bot_message_service() -> MagicMock:
    svc = MagicMock()
    svc.delete_message_from_chat = AsyncMock(return_value=True)
    svc.kick_chat_member = AsyncMock(return_value=True)
    return svc


@pytest.fixture
def mock_notify_usecase() -> MagicMock:
    uc = MagicMock()
    uc.execute = AsyncMock()
    return uc


def _resolve_bot_message_only(cls):
    from services.messaging.bot_message_service import BotMessageService

    if cls is BotMessageService:
        return mock_bot_message_service
    raise ValueError(f"Unexpected: {cls}")


@pytest.mark.asyncio
async def test_delete_message_from_chat_success(
    mock_bot_message_service: MagicMock,
) -> None:
    """delete_message_from_chat успешно удаляет сообщение."""
    mock_bot_message_service.delete_message_from_chat = AsyncMock(return_value=True)

    def resolve_fn(cls):
        from services.messaging.bot_message_service import BotMessageService

        if cls is BotMessageService:
            return mock_bot_message_service
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.moderation_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await delete_message_from_chat(chat_id=-100, message_id=123)

    mock_bot_message_service.delete_message_from_chat.assert_called_once_with(
        chat_id=-100, message_id=123
    )


@pytest.mark.asyncio
async def test_delete_message_from_chat_handles_exception(
    mock_bot_message_service: MagicMock,
) -> None:
    """delete_message_from_chat не пробрасывает исключение при ошибке."""
    mock_bot_message_service.delete_message_from_chat = AsyncMock(
        side_effect=RuntimeError("Message not found")
    )

    def resolve_fn(cls):
        from services.messaging.bot_message_service import BotMessageService

        if cls is BotMessageService:
            return mock_bot_message_service
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.moderation_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await delete_message_from_chat(chat_id=-100, message_id=123)

    mock_bot_message_service.delete_message_from_chat.assert_called_once()


@pytest.mark.asyncio
async def test_kick_unverified_member_task_message_deleted_kicks_user(
    mock_bot_message_service: MagicMock,
    mock_notify_usecase: MagicMock,
) -> None:
    """kick_unverified_member_task кикает пользователя когда сообщение удалено."""
    mock_bot_message_service.delete_message_from_chat = AsyncMock(return_value=True)
    mock_bot_message_service.kick_chat_member = AsyncMock(return_value=True)

    def resolve_fn(cls):
        from services.messaging.bot_message_service import BotMessageService
        from usecases.archive import NotifyArchiveChatMemberKickedUseCase

        if cls is BotMessageService:
            return mock_bot_message_service
        if cls is NotifyArchiveChatMemberKickedUseCase:
            return mock_notify_usecase
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.moderation_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await kick_unverified_member_task(
            chat_id=-100,
            message_id=456,
            user_id=789,
            username="testuser",
            chat_title="Test Chat",
        )

    mock_bot_message_service.delete_message_from_chat.assert_called_once_with(
        chat_id=-100, message_id=456
    )
    mock_bot_message_service.kick_chat_member.assert_called_once_with(
        chat_tg_id=-100, user_tg_id=789
    )
    mock_notify_usecase.execute.assert_called_once()


@pytest.mark.asyncio
async def test_kick_unverified_member_task_message_already_deleted_skips_kick(
    mock_bot_message_service: MagicMock,
) -> None:
    """kick_unverified_member_task не кикает когда сообщение уже удалено (верификация пройдена)."""
    mock_bot_message_service.delete_message_from_chat = AsyncMock(return_value=False)

    def resolve_fn(cls):
        from services.messaging.bot_message_service import BotMessageService

        if cls is BotMessageService:
            return mock_bot_message_service
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.moderation_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await kick_unverified_member_task(
            chat_id=-100,
            message_id=456,
            user_id=789,
            username="testuser",
            chat_title="Test Chat",
        )

    mock_bot_message_service.delete_message_from_chat.assert_called_once()
    mock_bot_message_service.kick_chat_member.assert_not_called()


@pytest.mark.asyncio
async def test_kick_unverified_member_task_kick_failed_no_notify(
    mock_bot_message_service: MagicMock,
    mock_notify_usecase: MagicMock,
) -> None:
    """kick_unverified_member_task не вызывает notify когда кик не удался."""
    mock_bot_message_service.delete_message_from_chat = AsyncMock(return_value=True)
    mock_bot_message_service.kick_chat_member = AsyncMock(return_value=False)

    def resolve_fn(cls):
        from services.messaging.bot_message_service import BotMessageService
        from usecases.archive import NotifyArchiveChatMemberKickedUseCase

        if cls is BotMessageService:
            return mock_bot_message_service
        if cls is NotifyArchiveChatMemberKickedUseCase:
            return mock_notify_usecase
        raise ValueError(f"Unexpected: {cls}")

    with patch("tasks.moderation_tasks.container") as mock_container:
        mock_container.resolve.side_effect = resolve_fn

        await kick_unverified_member_task(
            chat_id=-100,
            message_id=456,
            user_id=789,
            username="testuser",
            chat_title="Test Chat",
        )

    mock_bot_message_service.kick_chat_member.assert_called_once()
    mock_notify_usecase.execute.assert_not_called()
