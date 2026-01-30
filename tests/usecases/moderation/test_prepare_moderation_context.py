"""Tests for moderation context preparation and mapper fallbacks."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from constants.enums import UserRole
from constants.punishment import PunishmentActions as Actions
from dto import ModerationActionDTO
from mappers.moderation_mapper import map_message_to_moderation_dto
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
    user_service.get_or_create.assert_any_call(tg_id="10", username="hidden")
    user_service.get_or_create.assert_any_call(tg_id="20", username="admin")


def test_mapper_falls_back_to_hidden_username() -> None:
    now = datetime.utcnow()
    reply_user = SimpleNamespace(id=123, username=None)
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

    assert dto.violator_username == "hidden"
