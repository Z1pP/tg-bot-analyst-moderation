"""Tests for moderation context preparation and mapper fallbacks."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from constants.enums import UserRole
from constants.punishment import PunishmentActions as Actions
from dto import ModerationActionDTO
from mappers.moderation_mapper import map_message_to_moderation_dto
from models import User
from services import BotMessageService, BotPermissionService, ChatService, UserService
from usecases.moderation.base import ModerationUseCase


@pytest.mark.asyncio
async def test_prepare_context_uses_get_or_create() -> None:
    user_service = AsyncMock(spec=UserService)
    bot_message_service = AsyncMock(spec=BotMessageService)
    chat_service = AsyncMock(spec=ChatService)
    user_chat_status_repository = AsyncMock()
    permission_service = AsyncMock(spec=BotPermissionService)

    usecase = ModerationUseCase(
        user_service=user_service,
        bot_message_service=bot_message_service,
        chat_service=chat_service,
        user_chat_status_repository=user_chat_status_repository,
        permission_service=permission_service,
    )

    chat_service.get_chat_with_archive.return_value = SimpleNamespace(
        id=1,
        chat_id="100",
        title="Chat",
        archive_chat_id="200",
        archive_chat=SimpleNamespace(chat_id="200", title="Archive"),
    )
    permission_service.can_moderate.return_value = True
    permission_service.is_bot_in_chat.return_value = True
    permission_service.check_archive_permissions.return_value = SimpleNamespace(
        is_admin=True
    )
    permission_service.is_administrator.return_value = False

    violator = SimpleNamespace(id=10, tg_id="10", username="hidden", role=UserRole.USER)
    admin = SimpleNamespace(id=20, tg_id="20", username="admin", role=UserRole.ADMIN)
    user_service.get_or_create.side_effect = [violator, admin]

    dto = ModerationActionDTO(
        action=Actions.WARNING,
        violator_tgid="10",
        violator_username="hidden",
        admin_username="admin",
        admin_tgid="20",
        chat_tgid="100",
        chat_title="Chat",
        reply_message_id=1,
        original_message_id=None,
    )

    context = await usecase._prepare_moderation_context(dto=dto)

    assert context is not None
    assert context.violator == violator
    assert context.admin == admin
    # violator_username "hidden" в DTO превращается в "" при вызове get_or_create
    user_service.get_or_create.assert_any_call(tg_id="10", username="")
    user_service.get_or_create.assert_any_call(tg_id="20", username="admin")


def test_is_different_sender_true() -> None:
    """is_different_sender возвращает True при разных отправителях."""
    usecase = ModerationUseCase(
        user_service=AsyncMock(spec=UserService),
        bot_message_service=AsyncMock(spec=BotMessageService),
        chat_service=AsyncMock(spec=ChatService),
        user_chat_status_repository=AsyncMock(),
        permission_service=AsyncMock(spec=BotPermissionService),
    )
    assert usecase.is_different_sender(reply_user_tg_id="10", owner_tg_id="20") is True


def test_is_different_sender_false() -> None:
    """is_different_sender возвращает False при одном и том же отправителе."""
    usecase = ModerationUseCase(
        user_service=AsyncMock(spec=UserService),
        bot_message_service=AsyncMock(spec=BotMessageService),
        chat_service=AsyncMock(spec=ChatService),
        user_chat_status_repository=AsyncMock(),
        permission_service=AsyncMock(spec=BotPermissionService),
    )
    assert usecase.is_different_sender(reply_user_tg_id="10", owner_tg_id="10") is False


def test_is_bot_administrator_user() -> None:
    """is_bot_administrator возвращает False для USER."""
    usecase = ModerationUseCase(
        user_service=AsyncMock(spec=UserService),
        bot_message_service=AsyncMock(spec=BotMessageService),
        chat_service=AsyncMock(spec=ChatService),
        user_chat_status_repository=AsyncMock(),
        permission_service=AsyncMock(spec=BotPermissionService),
    )
    user = User(id=1, tg_id="1", username="u", role=UserRole.USER)
    assert usecase.is_bot_administrator(user) is False


def test_is_bot_administrator_admin() -> None:
    """is_bot_administrator возвращает True для ADMIN."""
    usecase = ModerationUseCase(
        user_service=AsyncMock(spec=UserService),
        bot_message_service=AsyncMock(spec=BotMessageService),
        chat_service=AsyncMock(spec=ChatService),
        user_chat_status_repository=AsyncMock(),
        permission_service=AsyncMock(spec=BotPermissionService),
    )
    user = User(id=1, tg_id="1", username="a", role=UserRole.ADMIN)
    assert usecase.is_bot_administrator(user) is True


def test_mapper_violator_username_from_reply() -> None:
    """Маппер берёт violator_username из reply_to_message.from_user (или пустую строку)."""
    from datetime import timezone

    now = datetime.now(timezone.utc)
    reply_user = SimpleNamespace(id=123, username="violator")
    reply_message = SimpleNamespace(
        from_user=reply_user,
        message_id=10,
        date=now,
    )
    message = SimpleNamespace(
        text="/warn reason",
        reply_to_message=reply_message,
        from_user=SimpleNamespace(id=1, username="admin"),
        chat=SimpleNamespace(id=99, title="Chat"),
        message_id=20,
        date=now,
    )

    dto = map_message_to_moderation_dto(message=message)

    assert dto.violator_username == "violator"
