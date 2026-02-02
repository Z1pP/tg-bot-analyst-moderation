"""Tests for GiveUserBanUseCase display-name formatting."""

from unittest.mock import AsyncMock

from services import (
    AdminActionLogService,
    BotMessageService,
    BotPermissionService,
    ChatService,
    PunishmentService,
    UserService,
)
from usecases.moderation.give_ban_user import GiveUserBanUseCase


def test_display_name_uses_id_when_username_missing() -> None:
    usecase = GiveUserBanUseCase(
        user_service=AsyncMock(spec=UserService),
        bot_message_service=AsyncMock(spec=BotMessageService),
        chat_service=AsyncMock(spec=ChatService),
        punishment_service=AsyncMock(spec=PunishmentService),
        user_chat_status_repository=AsyncMock(),
        permission_service=AsyncMock(spec=BotPermissionService),
        admin_action_log_service=AsyncMock(spec=AdminActionLogService),
    )

    name_token = usecase._get_violator_name_token(username=None, tg_id="123")
    display_name = usecase._get_violator_display_name(username=None, tg_id="123")

    assert name_token == "ID:123"
    assert display_name == "ID:123"


def test_display_name_uses_username_when_present() -> None:
    usecase = GiveUserBanUseCase(
        user_service=AsyncMock(spec=UserService),
        bot_message_service=AsyncMock(spec=BotMessageService),
        chat_service=AsyncMock(spec=ChatService),
        punishment_service=AsyncMock(spec=PunishmentService),
        user_chat_status_repository=AsyncMock(),
        permission_service=AsyncMock(spec=BotPermissionService),
        admin_action_log_service=AsyncMock(spec=AdminActionLogService),
    )

    name_token = usecase._get_violator_name_token(username="user", tg_id="123")
    display_name = usecase._get_violator_display_name(username="user", tg_id="123")

    assert name_token == "user"
    assert display_name == "@user"
