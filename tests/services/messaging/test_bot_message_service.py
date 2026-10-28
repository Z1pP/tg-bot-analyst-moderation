"""Характеризующие тесты BotMessageService.

Фиксируют текущее поведение: отправка/копирование/пересылка сообщений,
удаление, проверку прав can_moderate перед наказаниями и invite-ссылки.
"""

import asyncio
from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

from constants.punishment import PunishmentType
from exceptions.moderation import MessageTooOldError
from services.messaging.bot_message_service import BotMessageService
from services.permissions import BotPermissionService
from services.time_service import TimeZoneService


def _telegram_error(message: str = "Bad Request") -> TelegramAPIError:
    """Собирает TelegramAPIError без обращения к реальному Telegram."""
    return TelegramAPIError(method=MagicMock(), message=message)


def _bad_request(message: str = "Bad Request") -> TelegramBadRequest:
    """Собирает TelegramBadRequest с заданным текстом."""
    return TelegramBadRequest(method=MagicMock(), message=message)


@pytest.fixture
def mock_bot() -> AsyncMock:
    return AsyncMock(spec=Bot)


@pytest.fixture
def mock_permission_service() -> AsyncMock:
    return AsyncMock(spec=BotPermissionService)


@pytest.fixture
def service(
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> BotMessageService:
    return BotMessageService(
        bot=mock_bot,
        permission_service=mock_permission_service,
    )


# ---------------------------------------------------------------------------
# send_private_message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_private_message_success(
    service: BotMessageService,
    mock_bot: AsyncMock,
) -> None:
    """send_private_message отправляет HTML-сообщение с клавиатурой."""
    # Arrange
    markup = MagicMock()

    # Act
    result = await service.send_private_message(
        user_tgid=42,
        text="<b>hi</b>",
        reply_markup=markup,
    )

    # Assert
    assert result is None
    mock_bot.send_message.assert_awaited_once_with(
        chat_id=42,
        text="<b>hi</b>",
        parse_mode="HTML",
        reply_markup=markup,
    )


@pytest.mark.asyncio
async def test_send_private_message_swallows_telegram_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
) -> None:
    """Ошибка Telegram API при личной отправке проглатывается."""
    # Arrange
    mock_bot.send_message.side_effect = _telegram_error()

    # Act
    result = await service.send_private_message(user_tgid=42, text="hi")

    # Assert
    assert result is None
    mock_bot.send_message.assert_awaited_once()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "network_error",
    [OSError("down"), ConnectionError("down"), asyncio.TimeoutError()],
)
async def test_send_private_message_swallows_network_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
    network_error: Exception,
) -> None:
    """Сетевые ошибки при личной отправке проглатываются."""
    # Arrange
    mock_bot.send_message.side_effect = network_error

    # Act
    result = await service.send_private_message(user_tgid=42, text="hi")

    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# send_chat_message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_chat_message_success(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """send_chat_message возвращает отправленное сообщение при наличии прав."""
    # Arrange
    mock_permission_service.can_post_messages.return_value = True
    sent_message = MagicMock()
    mock_bot.send_message.return_value = sent_message

    # Act
    result = await service.send_chat_message(chat_tgid="-100", text="hi")

    # Assert
    assert result is sent_message
    mock_permission_service.can_post_messages.assert_awaited_once_with(
        chat_tgid="-100"
    )
    mock_bot.send_message.assert_awaited_once_with(
        chat_id="-100",
        text="hi",
        parse_mode="HTML",
        reply_markup=None,
    )


@pytest.mark.asyncio
async def test_send_chat_message_skipped_without_permission(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Без права отправки send_chat_message возвращает None и не зовёт bot."""
    # Arrange
    mock_permission_service.can_post_messages.return_value = False

    # Act
    result = await service.send_chat_message(chat_tgid="-100", text="hi")

    # Assert
    assert result is None
    mock_bot.send_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_chat_message_returns_none_on_telegram_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Ошибка Telegram API при отправке в чат возвращает None."""
    # Arrange
    mock_permission_service.can_post_messages.return_value = True
    mock_bot.send_message.side_effect = _telegram_error()

    # Act
    result = await service.send_chat_message(chat_tgid="-100", text="hi")

    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# copy_message / copy_message_as_reply
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_copy_message_returns_message_id(
    service: BotMessageService,
    mock_bot: AsyncMock,
) -> None:
    """copy_message возвращает message_id скопированного сообщения."""
    # Arrange
    mock_bot.copy_message.return_value = MagicMock(message_id=777)

    # Act
    result = await service.copy_message(
        chat_tgid="-100",
        from_chat_tgid="-200",
        message_id=5,
    )

    # Assert
    assert result == 777
    mock_bot.copy_message.assert_awaited_once_with(
        chat_id="-100",
        from_chat_id="-200",
        message_id=5,
    )


@pytest.mark.asyncio
async def test_copy_message_returns_none_on_telegram_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
) -> None:
    """Ошибка Telegram API при копировании возвращает None."""
    # Arrange
    mock_bot.copy_message.side_effect = _telegram_error()

    # Act
    result = await service.copy_message(
        chat_tgid="-100",
        from_chat_tgid="-200",
        message_id=5,
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_copy_message_returns_none_on_network_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
) -> None:
    """Сетевая ошибка при копировании возвращает None."""
    # Arrange
    mock_bot.copy_message.side_effect = OSError("down")

    # Act
    result = await service.copy_message(
        chat_tgid="-100",
        from_chat_tgid="-200",
        message_id=5,
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_copy_message_as_reply_passes_reply_to_message_id(
    service: BotMessageService,
    mock_bot: AsyncMock,
) -> None:
    """copy_message_as_reply передаёт reply_to_message_id и возвращает id."""
    # Arrange
    mock_bot.copy_message.return_value = MagicMock(message_id=888)

    # Act
    result = await service.copy_message_as_reply(
        chat_tgid="-100",
        from_chat_tgid="-200",
        message_id=5,
        reply_to_message_id=6,
    )

    # Assert
    assert result == 888
    mock_bot.copy_message.assert_awaited_once_with(
        chat_id="-100",
        from_chat_id="-200",
        message_id=5,
        reply_to_message_id=6,
    )


@pytest.mark.asyncio
async def test_copy_message_as_reply_returns_none_on_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
) -> None:
    """Ошибка Telegram API при копировании ответом возвращает None."""
    # Arrange
    mock_bot.copy_message.side_effect = _telegram_error()

    # Act
    result = await service.copy_message_as_reply(
        chat_tgid="-100",
        from_chat_tgid="-200",
        message_id=5,
        reply_to_message_id=6,
    )

    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# forward_message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_forward_message_success(
    service: BotMessageService,
    mock_bot: AsyncMock,
) -> None:
    """forward_message пересылает сообщение и возвращает None."""
    # Act
    result = await service.forward_message(
        chat_tgid="-100",
        from_chat_tgid="-200",
        message_tgid=5,
    )

    # Assert
    assert result is None
    mock_bot.forward_message.assert_awaited_once_with(
        chat_id="-100",
        from_chat_id="-200",
        message_id=5,
    )


@pytest.mark.asyncio
async def test_forward_message_swallows_message_id_invalid(
    service: BotMessageService,
    mock_bot: AsyncMock,
) -> None:
    """TelegramBadRequest с message_id_invalid проглатывается (пересылка пропущена)."""
    # Arrange
    mock_bot.forward_message.side_effect = _bad_request(
        "Bad Request: MESSAGE_ID_INVALID"
    )

    # Act
    result = await service.forward_message(
        chat_tgid="-100",
        from_chat_tgid="-200",
        message_tgid=5,
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_forward_message_swallows_telegram_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
) -> None:
    """Прочие ошибки Telegram API при пересылке проглатываются."""
    # Arrange
    mock_bot.forward_message.side_effect = _telegram_error()

    # Act
    result = await service.forward_message(
        chat_tgid="-100",
        from_chat_tgid="-200",
        message_tgid=5,
    )

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_forward_message_swallows_network_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
) -> None:
    """Сетевая ошибка при пересылке проглатывается."""
    # Arrange
    mock_bot.forward_message.side_effect = ConnectionError("down")

    # Act
    result = await service.forward_message(
        chat_tgid="-100",
        from_chat_tgid="-200",
        message_tgid=5,
    )

    # Assert
    assert result is None


# ---------------------------------------------------------------------------
# delete_message_from_chat
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_message_returns_bot_result(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """При наличии прав delete_message_from_chat возвращает результат bot."""
    # Arrange
    mock_permission_service.can_delete_messages.return_value = True
    mock_bot.delete_message.return_value = True

    # Act
    result = await service.delete_message_from_chat(chat_id="-100", message_id=5)

    # Assert
    assert result is True
    mock_bot.delete_message.assert_awaited_once_with(
        chat_id="-100",
        message_id=5,
    )


@pytest.mark.asyncio
async def test_delete_message_skipped_without_permission(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Без права удаления возвращается False и bot не вызывается."""
    # Arrange
    mock_permission_service.can_delete_messages.return_value = False

    # Act
    result = await service.delete_message_from_chat(chat_id="-100", message_id=5)

    # Assert
    assert result is False
    mock_bot.delete_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_message_returns_false_when_bot_returns_false(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Если bot.delete_message вернул False, сервис тоже возвращает False."""
    # Arrange
    mock_permission_service.can_delete_messages.return_value = True
    mock_bot.delete_message.return_value = False

    # Act
    result = await service.delete_message_from_chat(chat_id="-100", message_id=5)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_message_raises_when_older_than_48_hours(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Сообщение старше 48 часов поднимает MessageTooOldError до вызова bot."""
    # Arrange
    mock_permission_service.can_delete_messages.return_value = True
    old_date = TimeZoneService.now() - timedelta(hours=49)

    # Act / Assert
    with pytest.raises(MessageTooOldError):
        await service.delete_message_from_chat(
            chat_id="-100",
            message_id=5,
            message_date=old_date,
        )
    mock_bot.delete_message.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_message_allows_message_younger_than_48_hours(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Свежее сообщение проходит проверку возраста и удаляется."""
    # Arrange
    mock_permission_service.can_delete_messages.return_value = True
    mock_bot.delete_message.return_value = True
    recent_date = TimeZoneService.now() - timedelta(hours=47)

    # Act
    result = await service.delete_message_from_chat(
        chat_id="-100",
        message_id=5,
        message_date=recent_date,
    )

    # Assert
    assert result is True
    mock_bot.delete_message.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_message_already_deleted_returns_false(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """'message to delete not found' проглатывается и возвращает False."""
    # Arrange
    mock_permission_service.can_delete_messages.return_value = True
    mock_bot.delete_message.side_effect = _bad_request(
        "Bad Request: message to delete not found"
    )

    # Act
    result = await service.delete_message_from_chat(chat_id="-100", message_id=5)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_message_other_bad_request_returns_false(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Прочий TelegramBadRequest при удалении возвращает False."""
    # Arrange
    mock_permission_service.can_delete_messages.return_value = True
    mock_bot.delete_message.side_effect = _bad_request("Bad Request: chat not found")

    # Act
    result = await service.delete_message_from_chat(chat_id="-100", message_id=5)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_delete_message_network_error_returns_false(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Сетевая ошибка при удалении возвращает False."""
    # Arrange
    mock_permission_service.can_delete_messages.return_value = True
    mock_bot.delete_message.side_effect = asyncio.TimeoutError()

    # Act
    result = await service.delete_message_from_chat(chat_id="-100", message_id=5)

    # Assert
    assert result is False


# ---------------------------------------------------------------------------
# apply_punishment
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_punishment_mute_success(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """MUTE при наличии прав ограничивает участника и возвращает True."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.restrict_chat_member.return_value = True

    # Act
    result = await service.apply_punishment(
        chat_tg_id="-100",
        user_tg_id=42,
        action=PunishmentType.MUTE,
        duration_seconds=600,
    )

    # Assert
    assert result is True
    mock_bot.restrict_chat_member.assert_awaited_once()
    call_kwargs = mock_bot.restrict_chat_member.await_args.kwargs
    assert call_kwargs["chat_id"] == "-100"
    assert call_kwargs["user_id"] == 42
    assert call_kwargs["until_date"] == timedelta(seconds=600)
    assert call_kwargs["permissions"].can_send_messages is False


@pytest.mark.asyncio
async def test_apply_punishment_mute_checks_can_moderate_twice(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Текущее поведение: гейт can_moderate проверяется и в apply, и в mute."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.restrict_chat_member.return_value = True

    # Act
    await service.apply_punishment(
        chat_tg_id="-100",
        user_tg_id=42,
        action=PunishmentType.MUTE,
        duration_seconds=60,
    )

    # Assert
    assert mock_permission_service.can_moderate.await_count == 2


@pytest.mark.asyncio
async def test_apply_punishment_mute_skipped_without_permission(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """MUTE без права модерации возвращает False и не зовёт bot."""
    # Arrange
    mock_permission_service.can_moderate.return_value = False

    # Act
    result = await service.apply_punishment(
        chat_tg_id="-100",
        user_tg_id=42,
        action=PunishmentType.MUTE,
        duration_seconds=600,
    )

    # Assert
    assert result is False
    mock_bot.restrict_chat_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_apply_punishment_ban_success(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """BAN при наличии прав банит участника и возвращает True."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.ban_chat_member.return_value = True

    # Act
    result = await service.apply_punishment(
        chat_tg_id="-100",
        user_tg_id=42,
        action=PunishmentType.BAN,
    )

    # Assert
    assert result is True
    mock_bot.ban_chat_member.assert_awaited_once_with(
        chat_id="-100",
        user_id=42,
    )


@pytest.mark.asyncio
async def test_apply_punishment_ban_skipped_without_permission(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """BAN без права модерации возвращает False и не зовёт bot."""
    # Arrange
    mock_permission_service.can_moderate.return_value = False

    # Act
    result = await service.apply_punishment(
        chat_tg_id="-100",
        user_tg_id=42,
        action=PunishmentType.BAN,
    )

    # Assert
    assert result is False
    mock_bot.ban_chat_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_apply_punishment_warning_returns_true_without_checks(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """WARNING не требует прав и не обращается к bot."""
    # Act
    result = await service.apply_punishment(
        chat_tg_id="-100",
        user_tg_id=42,
        action=PunishmentType.WARNING,
    )

    # Assert
    assert result is True
    mock_permission_service.can_moderate.assert_not_awaited()
    mock_bot.restrict_chat_member.assert_not_awaited()
    mock_bot.ban_chat_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_apply_punishment_unknown_action_raises_value_error(
    service: BotMessageService,
) -> None:
    """Неизвестное действие поднимает ValueError."""
    # Act / Assert
    with pytest.raises(ValueError, match="Неизвестное действие"):
        await service.apply_punishment(
            chat_tg_id="-100",
            user_tg_id=42,
            action="delete",  # type: ignore[arg-type]
        )


@pytest.mark.asyncio
async def test_apply_punishment_returns_false_on_telegram_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Ошибка Telegram API при применении наказания возвращает False."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.ban_chat_member.side_effect = _telegram_error()

    # Act
    result = await service.apply_punishment(
        chat_tg_id="-100",
        user_tg_id=42,
        action=PunishmentType.BAN,
    )

    # Assert
    assert result is False


# ---------------------------------------------------------------------------
# mute / ban / unban / kick / unmute
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_mute_skipped_without_permission(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """mute без права модерации возвращает False и не зовёт bot."""
    # Arrange
    mock_permission_service.can_moderate.return_value = False

    # Act
    result = await service.mute_chat_member(
        chat_tg_id="-100",
        user_tg_id=42,
        duration_seconds=60,
    )

    # Assert
    assert result is False
    mock_bot.restrict_chat_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_mute_success_passes_permissions_and_until_date(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """mute ограничивает все права на заданный срок."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.restrict_chat_member.return_value = True

    # Act
    result = await service.mute_chat_member(
        chat_tg_id="-100",
        user_tg_id=42,
        duration_seconds=120,
    )

    # Assert
    assert result is True
    call_kwargs = mock_bot.restrict_chat_member.await_args.kwargs
    assert call_kwargs["chat_id"] == "-100"
    assert call_kwargs["user_id"] == 42
    assert call_kwargs["until_date"] == timedelta(seconds=120)
    permissions = call_kwargs["permissions"]
    assert permissions.can_send_messages is False
    assert permissions.can_send_media_messages is False
    assert permissions.can_invite_users is False


@pytest.mark.asyncio
async def test_mute_returns_false_on_telegram_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Ошибка Telegram API при муте возвращает False."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.restrict_chat_member.side_effect = _telegram_error()

    # Act
    result = await service.mute_chat_member(
        chat_tg_id="-100",
        user_tg_id=42,
        duration_seconds=60,
    )

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_ban_skipped_without_permission(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """ban без права модерации возвращает False и не зовёт bot."""
    # Arrange
    mock_permission_service.can_moderate.return_value = False

    # Act
    result = await service.ban_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is False
    mock_bot.ban_chat_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_ban_success(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """ban с правами возвращает результат bot."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.ban_chat_member.return_value = True

    # Act
    result = await service.ban_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is True
    mock_bot.ban_chat_member.assert_awaited_once_with(
        chat_id="-100",
        user_id=42,
    )


@pytest.mark.asyncio
async def test_ban_returns_false_on_telegram_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Ошибка Telegram API при бане возвращает False."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.ban_chat_member.side_effect = _telegram_error()

    # Act
    result = await service.ban_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_unban_skipped_without_permission(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """unban без права модерации возвращает False и не зовёт bot."""
    # Arrange
    mock_permission_service.can_moderate.return_value = False

    # Act
    result = await service.unban_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is False
    mock_bot.unban_chat_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_unban_success_passes_only_if_banned(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """unban вызывает bot.unban_chat_member с only_if_banned=True."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.unban_chat_member.return_value = True

    # Act
    result = await service.unban_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is True
    mock_bot.unban_chat_member.assert_awaited_once_with(
        chat_id="-100",
        user_id=42,
        only_if_banned=True,
    )


@pytest.mark.asyncio
async def test_unban_returns_false_on_telegram_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Ошибка Telegram API при разбане возвращает False."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.unban_chat_member.side_effect = _telegram_error()

    # Act
    result = await service.unban_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_kick_bans_then_unbans(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """kick = ban + unban, оба вызова уходят в bot."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.ban_chat_member.return_value = True
    mock_bot.unban_chat_member.return_value = True

    # Act
    result = await service.kick_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is True
    mock_bot.ban_chat_member.assert_awaited_once_with(
        chat_id="-100",
        user_id=42,
    )
    mock_bot.unban_chat_member.assert_awaited_once_with(
        chat_id="-100",
        user_id=42,
        only_if_banned=True,
    )


@pytest.mark.asyncio
async def test_kick_returns_false_and_skips_unban_when_ban_fails(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Если ban не удался, unban не вызывается."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.ban_chat_member.return_value = False

    # Act
    result = await service.kick_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is False
    mock_bot.unban_chat_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_kick_skipped_without_permission(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """kick без права модерации не трогает bot."""
    # Arrange
    mock_permission_service.can_moderate.return_value = False

    # Act
    result = await service.kick_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is False
    mock_bot.ban_chat_member.assert_not_awaited()
    mock_bot.unban_chat_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_unmute_skipped_without_permission(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """unmute без права модерации возвращает False и не зовёт bot."""
    # Arrange
    mock_permission_service.can_moderate.return_value = False

    # Act
    result = await service.unmute_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is False
    mock_bot.restrict_chat_member.assert_not_awaited()


@pytest.mark.asyncio
async def test_unmute_restores_permissions_without_until_date(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """unmute выдаёт полные права и не передаёт until_date."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.restrict_chat_member.return_value = True

    # Act
    result = await service.unmute_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is True
    call_kwargs = mock_bot.restrict_chat_member.await_args.kwargs
    assert call_kwargs["chat_id"] == "-100"
    assert call_kwargs["user_id"] == 42
    assert "until_date" not in call_kwargs
    assert call_kwargs["permissions"].can_send_messages is True


@pytest.mark.asyncio
async def test_unmute_returns_false_on_telegram_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Ошибка Telegram API при размуте возвращает False."""
    # Arrange
    mock_permission_service.can_moderate.return_value = True
    mock_bot.restrict_chat_member.side_effect = _telegram_error()

    # Act
    result = await service.unmute_chat_member(chat_tg_id="-100", user_tg_id=42)

    # Assert
    assert result is False


# ---------------------------------------------------------------------------
# get_chat_invite_link
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_chat_invite_link_skipped_without_permission(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Без права приглашать ссылка не запрашивается."""
    # Arrange
    mock_permission_service.can_invite_users.return_value = False

    # Act
    result = await service.get_chat_invite_link(chat_tgid="-100")

    # Assert
    assert result is None
    mock_bot.export_chat_invite_link.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_chat_invite_link_returns_object_attribute(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Если Telegram вернул объект с invite_link, возвращается его значение."""
    # Arrange
    mock_permission_service.can_invite_users.return_value = True
    mock_bot.export_chat_invite_link.return_value = MagicMock(
        invite_link="https://t.me/+abc"
    )

    # Act
    result = await service.get_chat_invite_link(chat_tgid="-100")

    # Assert
    assert result == "https://t.me/+abc"
    mock_bot.export_chat_invite_link.assert_awaited_once_with(chat_id="-100")


@pytest.mark.asyncio
async def test_get_chat_invite_link_returns_plain_string(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Строковый ответ возвращается как есть."""
    # Arrange
    mock_permission_service.can_invite_users.return_value = True
    mock_bot.export_chat_invite_link.return_value = "https://t.me/+str"

    # Act
    result = await service.get_chat_invite_link(chat_tgid="-100")

    # Assert
    assert result == "https://t.me/+str"


@pytest.mark.asyncio
async def test_get_chat_invite_link_returns_none_for_unexpected_result(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Неожиданный результат без invite_link даёт None."""
    # Arrange
    mock_permission_service.can_invite_users.return_value = True
    mock_bot.export_chat_invite_link.return_value = None

    # Act
    result = await service.get_chat_invite_link(chat_tgid="-100")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_chat_invite_link_returns_none_on_telegram_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Ошибка Telegram API при экспорте ссылки возвращает None."""
    # Arrange
    mock_permission_service.can_invite_users.return_value = True
    mock_bot.export_chat_invite_link.side_effect = _telegram_error()

    # Act
    result = await service.get_chat_invite_link(chat_tgid="-100")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_chat_invite_link_returns_none_on_network_error(
    service: BotMessageService,
    mock_bot: AsyncMock,
    mock_permission_service: AsyncMock,
) -> None:
    """Сетевая ошибка при экспорте ссылки возвращает None."""
    # Arrange
    mock_permission_service.can_invite_users.return_value = True
    mock_bot.export_chat_invite_link.side_effect = OSError("down")

    # Act
    result = await service.get_chat_invite_link(chat_tgid="-100")

    # Assert
    assert result is None