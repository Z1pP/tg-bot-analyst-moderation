"""Тесты BotPermissionService."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.exceptions import TelegramAPIError
from aiogram.types import (
    Chat,
    ChatMemberAdministrator,
    ChatMemberBanned,
    ChatMemberOwner,
    ChatMemberRestricted,
)

from services.permissions.bot_permission import (
    BotPermissionService,
    BotPermissionsCheck,
    ChatMemberStatus,
)


@pytest.fixture
def mock_bot() -> MagicMock:
    """Мок бота aiogram."""
    bot = MagicMock()
    bot.id = 12345
    return bot


@pytest.fixture
def bot_permission_service(mock_bot: MagicMock) -> BotPermissionService:
    """Сервис с замоканным ботом."""
    return BotPermissionService(bot=mock_bot)


@pytest.mark.asyncio
async def test_get_total_members_success(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_total_members возвращает количество участников при успехе."""
    mock_bot.get_chat_member_count = AsyncMock(return_value=42)

    result = await bot_permission_service.get_total_members(chat_tgid="-100")

    assert result == 42
    mock_bot.get_chat_member_count.assert_called_once_with(chat_id="-100")


@pytest.mark.asyncio
async def test_get_total_members_api_error_returns_zero(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_total_members возвращает 0 при TelegramAPIError."""
    mock_bot.get_chat_member_count = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "error")
    )

    result = await bot_permission_service.get_total_members(chat_tgid="-100")

    assert result == 0


@pytest.mark.asyncio
async def test_get_chat_member_status_banned(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_chat_member_status возвращает is_banned=True для забаненного."""
    member = MagicMock(spec=ChatMemberBanned)
    member.until_date = datetime(2025, 12, 31, 12, 0)
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.get_chat_member_status(
        user_id=1, chat_tgid="-100"
    )

    assert result.is_banned is True
    assert result.is_muted is False
    assert result.banned_until is not None


@pytest.mark.asyncio
async def test_get_chat_member_status_restricted_muted(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_chat_member_status возвращает is_muted=True для замьюченного."""
    member = MagicMock(spec=ChatMemberRestricted)
    member.can_send_messages = False
    member.until_date = datetime(2025, 12, 31, 12, 0)
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.get_chat_member_status(
        user_id=1, chat_tgid="-100"
    )

    assert result.is_muted is True
    assert result.is_banned is False
    assert result.muted_until is not None


@pytest.mark.asyncio
async def test_get_chat_member_status_api_error_returns_empty(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_chat_member_status возвращает пустой статус при API ошибке."""
    mock_bot.get_chat_member = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "error")
    )

    result = await bot_permission_service.get_chat_member_status(
        user_id=1, chat_tgid="-100"
    )

    assert result.is_banned is False
    assert result.is_muted is False
    assert result.banned_until is None
    assert result.muted_until is None


@pytest.mark.asyncio
async def test_get_bot_member_success(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_bot_member возвращает участника при успехе."""
    member = MagicMock()
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.get_bot_member(chat_tgid="-100")

    assert result is member
    mock_bot.get_chat_member.assert_called_once_with(
        chat_id="-100", user_id=mock_bot.id
    )


@pytest.mark.asyncio
async def test_get_bot_member_api_error_returns_none(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_bot_member возвращает None при API ошибке."""
    mock_bot.get_chat_member = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "error")
    )

    result = await bot_permission_service.get_bot_member(chat_tgid="-100")

    assert result is None


@pytest.mark.asyncio
async def test_get_chat_from_telegram_success(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_chat_from_telegram возвращает чат при успехе."""
    chat = MagicMock(spec=Chat)
    chat.type = "supergroup"
    mock_bot.get_chat = AsyncMock(return_value=chat)

    result = await bot_permission_service.get_chat_from_telegram(chat_tgid="-100")

    assert result is chat


@pytest.mark.asyncio
async def test_get_chat_from_telegram_api_error_returns_none(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_chat_from_telegram возвращает None при API ошибке."""
    mock_bot.get_chat = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "error")
    )

    result = await bot_permission_service.get_chat_from_telegram(chat_tgid="-100")

    assert result is None


@pytest.mark.asyncio
async def test_is_channel_true(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_channel возвращает True для канала."""
    chat = MagicMock(spec=Chat)
    chat.type = "channel"
    mock_bot.get_chat = AsyncMock(return_value=chat)

    result = await bot_permission_service.is_channel(chat_tgid="-100")

    assert result is True


@pytest.mark.asyncio
async def test_is_channel_false_for_group(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_channel возвращает False для группы."""
    chat = MagicMock(spec=Chat)
    chat.type = "supergroup"
    mock_bot.get_chat = AsyncMock(return_value=chat)

    result = await bot_permission_service.is_channel(chat_tgid="-100")

    assert result is False


@pytest.mark.asyncio
async def test_is_channel_none_chat_returns_false(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_channel возвращает False для None чата."""
    mock_bot.get_chat = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "error")
    )

    result = await bot_permission_service.is_channel(chat_tgid="-100")

    assert result is False


@pytest.mark.asyncio
async def test_is_bot_in_chat_true(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_bot_in_chat возвращает True когда бот в чате."""
    member = MagicMock()
    member.status = "administrator"
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.is_bot_in_chat(chat_tgid="-100")

    assert result is True


@pytest.mark.asyncio
async def test_is_bot_in_chat_false_when_left(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_bot_in_chat возвращает False когда бот вышел."""
    member = MagicMock()
    member.status = "left"
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.is_bot_in_chat(chat_tgid="-100")

    assert result is False


@pytest.mark.asyncio
async def test_is_bot_in_chat_false_when_no_member(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_bot_in_chat возвращает False когда бот не найден."""
    mock_bot.get_chat_member = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "error")
    )

    result = await bot_permission_service.is_bot_in_chat(chat_tgid="-100")

    assert result is False


@pytest.mark.asyncio
async def test_can_moderate_true_for_owner(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """can_moderate возвращает True для владельца чата."""
    member = MagicMock(spec=ChatMemberOwner)
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.can_moderate(chat_tgid="-100")

    assert result is True


@pytest.mark.asyncio
async def test_can_moderate_true_for_admin_with_permission(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """can_moderate возвращает True для админа с правами."""
    member = MagicMock(spec=ChatMemberAdministrator)
    member.can_restrict_members = True
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.can_moderate(chat_tgid="-100")

    assert result is True


@pytest.mark.asyncio
async def test_can_moderate_false_for_admin_without_permission(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """can_moderate возвращает False для админа без прав."""
    member = MagicMock(spec=ChatMemberAdministrator)
    member.can_restrict_members = False
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.can_moderate(chat_tgid="-100")

    assert result is False


@pytest.mark.asyncio
async def test_is_administrator_true(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_administrator возвращает True для админа."""
    member = MagicMock(spec=ChatMemberAdministrator)
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.is_administrator(
        user_id=1, chat_tgid="-100"
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_administrator_false_on_api_error(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_administrator возвращает False при API ошибке."""
    mock_bot.get_chat_member = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "error")
    )

    result = await bot_permission_service.is_administrator(
        user_id=1, chat_tgid="-100"
    )

    assert result is False


@pytest.mark.asyncio
async def test_get_member_username_returns_username(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_member_username возвращает username участника."""
    user = MagicMock()
    user.username = "violator"
    member = MagicMock()
    member.user = user
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.get_member_username(
        user_id=42, chat_tgid="-100"
    )

    assert result == "violator"


@pytest.mark.asyncio
async def test_get_member_username_empty_on_api_error(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_member_username возвращает пустую строку при ошибке API."""
    mock_bot.get_chat_member = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "error")
    )

    result = await bot_permission_service.get_member_username(
        user_id=42, chat_tgid="-100"
    )

    assert result == ""


@pytest.mark.asyncio
async def test_is_member_banned_true(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_member_banned возвращает True для забаненного."""
    member = MagicMock(spec=ChatMemberBanned)
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.is_member_banned(
        user_id=1, chat_tgid="-100"
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_member_banned_false_on_api_error(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_member_banned возвращает False при API ошибке."""
    mock_bot.get_chat_member = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "error")
    )

    result = await bot_permission_service.is_member_banned(
        user_id=1, chat_tgid="-100"
    )

    assert result is False


@pytest.mark.asyncio
async def test_is_member_muted_true(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_member_muted возвращает True для замьюченного."""
    member = MagicMock(spec=ChatMemberRestricted)
    member.can_send_messages = False
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.is_member_muted(
        user_id=1, chat_tgid="-100"
    )

    assert result is True


@pytest.mark.asyncio
async def test_is_member_muted_false_on_api_error(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """is_member_muted возвращает False при API ошибке."""
    mock_bot.get_chat_member = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "error")
    )

    result = await bot_permission_service.is_member_muted(
        user_id=1, chat_tgid="-100"
    )

    assert result is False


@pytest.mark.asyncio
async def test_check_archive_permissions_not_member(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """check_archive_permissions возвращает is_member=False при отсутствии бота."""
    mock_bot.get_chat_member = AsyncMock(
        side_effect=TelegramAPIError(MagicMock(), "error")
    )

    result = await bot_permission_service.check_archive_permissions(chat_tgid="-100")

    assert isinstance(result, BotPermissionsCheck)
    assert result.is_member is False
    assert result.is_admin is False
    assert result.has_all_permissions is False
    assert "Не удалось получить статус бота" in result.missing_permissions


@pytest.mark.asyncio
async def test_check_archive_permissions_owner_has_all(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """check_archive_permissions для владельца возвращает has_all_permissions=True."""
    member = MagicMock(spec=ChatMemberOwner)
    member.status = "creator"
    mock_bot.get_chat_member = AsyncMock(return_value=member)
    mock_bot.get_chat = AsyncMock(return_value=MagicMock(type="supergroup"))

    result = await bot_permission_service.check_archive_permissions(chat_tgid="-100")

    assert result.is_admin is True
    assert result.has_all_permissions is True
    assert result.missing_permissions == []


@pytest.mark.asyncio
async def test_chat_member_status_dataclass() -> None:
    """ChatMemberStatus корректно инициализируется."""
    status = ChatMemberStatus(is_banned=True, is_muted=False)
    assert status.is_banned is True
    assert status.is_muted is False
    assert status.banned_until is None


@pytest.mark.asyncio
async def test_can_post_messages_true_for_channel_with_permission(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """can_post_messages возвращает True для канала с правом can_post_messages."""
    member = MagicMock(spec=ChatMemberAdministrator)
    member.can_post_messages = True
    chat = MagicMock(spec=Chat)
    chat.type = "channel"
    mock_bot.get_chat = AsyncMock(return_value=chat)
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.can_post_messages(chat_tgid="-100")

    assert result is True


@pytest.mark.asyncio
async def test_can_post_messages_false_for_channel_without_permission(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """can_post_messages возвращает False для канала без права can_post_messages."""
    member = MagicMock(spec=ChatMemberAdministrator)
    member.can_post_messages = False
    chat = MagicMock(spec=Chat)
    chat.type = "channel"
    mock_bot.get_chat = AsyncMock(return_value=chat)
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.can_post_messages(chat_tgid="-100")

    assert result is False


@pytest.mark.asyncio
async def test_can_post_messages_true_for_group_member(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """can_post_messages возвращает True для обычного участника группы."""
    member = MagicMock()
    member.status = "member"
    chat = MagicMock(spec=Chat)
    chat.type = "supergroup"
    mock_bot.get_chat = AsyncMock(return_value=chat)
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.can_post_messages(chat_tgid="-100")

    assert result is True


@pytest.mark.asyncio
async def test_can_post_messages_false_for_restricted_without_send(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """can_post_messages возвращает False для restricted без can_send_messages."""
    member = MagicMock(spec=ChatMemberRestricted)
    member.status = "restricted"
    member.can_send_messages = False
    chat = MagicMock(spec=Chat)
    chat.type = "supergroup"
    mock_bot.get_chat = AsyncMock(return_value=chat)
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.can_post_messages(chat_tgid="-100")

    assert result is False


@pytest.mark.asyncio
async def test_check_archive_permissions_admin_with_missing_permissions(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """check_archive_permissions для админа без can_delete_messages."""
    member = MagicMock(spec=ChatMemberAdministrator)
    member.status = "administrator"
    member.can_restrict_members = True
    member.can_invite_users = True
    member.can_delete_messages = False
    member.can_post_messages = True
    chat = MagicMock(spec=Chat)
    chat.type = "channel"
    mock_bot.get_chat_member = AsyncMock(return_value=member)
    mock_bot.get_chat = AsyncMock(return_value=chat)

    result = await bot_permission_service.check_archive_permissions(chat_tgid="-100")

    assert result.is_admin is True
    assert result.has_all_permissions is False
    assert "Удаление сообщений" in result.missing_permissions


@pytest.mark.asyncio
async def test_get_chat_member_status_banned_without_until_date(
    bot_permission_service: BotPermissionService,
    mock_bot: MagicMock,
) -> None:
    """get_chat_member_status для ChatMemberBanned без until_date."""
    member = MagicMock(spec=ChatMemberBanned)
    member.until_date = None
    mock_bot.get_chat_member = AsyncMock(return_value=member)

    result = await bot_permission_service.get_chat_member_status(
        user_id=1, chat_tgid="-100"
    )

    assert result.is_banned is True
    assert result.banned_until is None
