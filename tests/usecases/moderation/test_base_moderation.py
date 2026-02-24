"""Тесты для usecases/moderation/base.py: _verify_bot_permissions, _cleanup_chat_messages, _notify_participants, _finalize_moderation."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from constants.enums import UserRole
from exceptions.moderation import (
    BotInsufficientPermissionsError,
    BotNoAdminRightsInArchiveChatError,
    BotNotInArchiveChatError,
    MessageTooOldError,
)
from services import BotMessageService, BotPermissionService, ChatService, UserService
from usecases.moderation.base import ModerationContext, ModerationUseCase


@pytest.fixture
def base_usecase() -> ModerationUseCase:
    return ModerationUseCase(
        user_service=AsyncMock(spec=UserService),
        bot_message_service=AsyncMock(spec=BotMessageService),
        chat_service=AsyncMock(spec=ChatService),
        user_chat_status_repository=AsyncMock(),
        permission_service=AsyncMock(spec=BotPermissionService),
    )


@pytest.fixture
def sample_context() -> ModerationContext:
    admin = SimpleNamespace(id=1, tg_id="1", username="admin", role=UserRole.ADMIN)
    violator = SimpleNamespace(id=2, tg_id="2", username="u", role=UserRole.USER)
    chat = SimpleNamespace(id=1, chat_id="100", title="Chat")
    archive_chat = SimpleNamespace(chat_id="200", title="Archive")
    dto = SimpleNamespace(
        chat_tgid="100",
        from_admin_panel=False,
        reply_message_id=10,
        reply_message_date=None,
    )
    return ModerationContext(
        dto=dto,
        violator=violator,
        admin=admin,
        chat=chat,
        archive_chat=archive_chat,
    )


@pytest.mark.asyncio
async def test_verify_bot_permissions_raises_insufficient(
    base_usecase: ModerationUseCase,
) -> None:
    """При отсутствии прав модерации в чате выбрасывается BotInsufficientPermissionsError."""
    chat = SimpleNamespace(
        chat_id="100", title="Test", archive_chat_id="200", archive_chat=None
    )
    base_usecase.permission_service.can_moderate.return_value = False

    with pytest.raises(BotInsufficientPermissionsError) as exc_info:
        await base_usecase._verify_bot_permissions(chat)
    assert "Test" in str(exc_info.value) or "Test" in exc_info.value.get_user_message()


@pytest.mark.asyncio
async def test_verify_bot_permissions_raises_not_in_archive(
    base_usecase: ModerationUseCase,
) -> None:
    """Если бот не в архивном чате — BotNotInArchiveChatError."""
    chat = SimpleNamespace(
        chat_id="100",
        title="Test",
        archive_chat_id="200",
        archive_chat=SimpleNamespace(title="Archive"),
    )
    base_usecase.permission_service.can_moderate.return_value = True
    base_usecase.permission_service.is_bot_in_chat.return_value = False

    with pytest.raises(BotNotInArchiveChatError):
        await base_usecase._verify_bot_permissions(chat)


@pytest.mark.asyncio
async def test_verify_bot_permissions_raises_no_admin_in_archive(
    base_usecase: ModerationUseCase,
) -> None:
    """Если бот не админ в архивном чате — BotNoAdminRightsInArchiveChatError."""
    chat = SimpleNamespace(
        chat_id="100",
        title="Test",
        archive_chat_id="200",
        archive_chat=SimpleNamespace(title="Archive"),
    )
    base_usecase.permission_service.can_moderate.return_value = True
    base_usecase.permission_service.is_bot_in_chat.return_value = True
    base_usecase.permission_service.check_archive_permissions.return_value = (
        SimpleNamespace(is_admin=False)
    )

    with pytest.raises(BotNoAdminRightsInArchiveChatError):
        await base_usecase._verify_bot_permissions(chat)


@pytest.mark.asyncio
async def test_cleanup_chat_messages_from_admin_panel_returns_unchanged(
    base_usecase: ModerationUseCase, sample_context: ModerationContext
) -> None:
    """При from_admin_panel удаление не вызывается, текст не меняется."""
    sample_context.dto.from_admin_panel = True
    deleted, text = await base_usecase._cleanup_chat_messages(
        sample_context, "Отчёт удалено"
    )
    assert deleted is False
    assert text == "Отчёт удалено"
    base_usecase.bot_message_service.delete_message_from_chat.assert_not_called()


@pytest.mark.asyncio
async def test_cleanup_chat_messages_message_too_old_sends_notification(
    base_usecase: ModerationUseCase, sample_context: ModerationContext
) -> None:
    """При MessageTooOldError отправляется уведомление админу и текст отчёта меняется."""
    base_usecase.bot_message_service.delete_message_from_chat.side_effect = (
        MessageTooOldError("Сообщение старше 48 часов")
    )
    deleted, text = await base_usecase._cleanup_chat_messages(
        sample_context, "сообщение удалено"
    )
    assert deleted is False
    assert "не удалено" in text and "48" in text
    base_usecase.bot_message_service.send_private_message.assert_called_once()
    call_kw = base_usecase.bot_message_service.send_private_message.call_args.kwargs
    assert call_kw["user_tgid"] == "1"


@pytest.mark.asyncio
async def test_notify_participants_sends_reason_and_admin_message(
    base_usecase: ModerationUseCase, sample_context: ModerationContext
) -> None:
    """Отправляется reason в чат и admin_answer в ЛС."""
    with patch(
        "tasks.moderation_tasks.delete_message_from_chat.kiq",
        new_callable=AsyncMock,
    ):
        await base_usecase._notify_participants(
            sample_context,
            reason_text="Нарушитель наказан",
            admin_answer_text="Готово",
        )
    base_usecase.bot_message_service.send_chat_message.assert_called_once_with(
        chat_tgid="100", text="Нарушитель наказан"
    )
    base_usecase.bot_message_service.send_private_message.assert_called_once_with(
        user_tgid="1", text="Готово"
    )


@pytest.mark.asyncio
async def test_notify_participants_skips_private_if_from_admin_panel(
    base_usecase: ModerationUseCase, sample_context: ModerationContext
) -> None:
    """При from_admin_panel в ЛС админу не отправляется."""
    sample_context.dto.from_admin_panel = True
    with patch(
        "tasks.moderation_tasks.delete_message_from_chat.kiq",
        new_callable=AsyncMock,
    ):
        await base_usecase._notify_participants(
            sample_context,
            reason_text="Причина",
            admin_answer_text="Ответ админу",
        )
    base_usecase.bot_message_service.send_chat_message.assert_called_once()
    base_usecase.bot_message_service.send_private_message.assert_not_called()


@pytest.mark.asyncio
async def test_finalize_moderation_calls_forward_cleanup_archive_notify(
    base_usecase: ModerationUseCase, sample_context: ModerationContext
) -> None:
    """_finalize_moderation вызывает forward, cleanup, archive, notify."""
    base_usecase.bot_message_service.delete_message_from_chat.return_value = True
    with patch(
        "tasks.moderation_tasks.delete_message_from_chat.kiq",
        new_callable=AsyncMock,
    ):
        await base_usecase._finalize_moderation(
            context=sample_context,
            report_text="Отчёт",
            reason_text="Причина",
            admin_answer_text="",
        )
    base_usecase.bot_message_service.forward_message.assert_called_once_with(
        chat_tgid="200",
        from_chat_tgid="100",
        message_tgid=10,
    )
    # send_chat_message вызывается для архива (отчёт) и для чата (причина)
    assert base_usecase.bot_message_service.send_chat_message.call_count >= 1
    base_usecase.bot_message_service.send_chat_message.assert_any_call(
        chat_tgid="200", text="Отчёт"
    )
    assert sample_context.message_deleted is True
