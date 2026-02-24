"""Тесты для VerifyMemberUseCase: проверка наказаний и возврат ResultVerifyMember."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from constants import Dialog
from constants.punishment import PunishmentType
from dto import ResultVerifyMember
from usecases.moderation.verify_member import VerifyMemberUseCase


@pytest.fixture
def usecase() -> VerifyMemberUseCase:
    return VerifyMemberUseCase(
        bot_message_service=AsyncMock(),
        bot_permission_service=AsyncMock(),
        chat_service=AsyncMock(),
        user_service=AsyncMock(),
        punishment_service=AsyncMock(),
        punishment_ladder_repository=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_execute_no_punishments_unmutes_and_returns_success(
    usecase: VerifyMemberUseCase,
) -> None:
    """При отсутствии наказаний: unmute вызывается, возвращается VERIFIED_SUCCESS."""
    usecase.bot_permission_service.can_moderate.return_value = True
    chat = SimpleNamespace(id=1, chat_id="-100123")
    usecase.chat_service.get_chat.return_value = chat
    usecase.user_service.get_user.return_value = None  # новый пользователь
    usecase.punishment_service.get_punishment_count = AsyncMock(return_value=0)
    usecase.bot_message_service.unmute_chat_member.return_value = True

    result = await usecase.execute(user_tgid="123", chat_tgid="-100123")

    assert isinstance(result, ResultVerifyMember)
    assert result.unmuted is True
    assert result.message == Dialog.Antibot.VERIFIED_SUCCESS
    usecase.bot_message_service.unmute_chat_member.assert_called_once_with(
        chat_tg_id="-100123",
        user_tg_id="123",
    )


@pytest.mark.asyncio
async def test_execute_has_punishments_returns_message_no_unmute(
    usecase: VerifyMemberUseCase,
) -> None:
    """При наличии наказаний: unmute не вызывается, возвращается сообщение о наказании."""
    usecase.bot_permission_service.can_moderate.return_value = True
    chat = SimpleNamespace(id=1, chat_id="-100123")
    usecase.chat_service.get_chat.return_value = chat
    user = SimpleNamespace(id=5)
    usecase.user_service.get_user.return_value = user
    usecase.punishment_service.get_punishment_count = AsyncMock(return_value=2)
    next_ladder = SimpleNamespace(
        punishment_type=PunishmentType.MUTE,
        duration_seconds=3600,
    )
    usecase.punishment_ladder_repository.get_punishment_by_step = AsyncMock(
        return_value=next_ladder
    )

    result = await usecase.execute(user_tgid="123", chat_tgid="-100123")

    assert isinstance(result, ResultVerifyMember)
    assert result.unmuted is False
    assert "2 предупреждений" in result.message
    assert "мут" in result.message or "предупреждение" in result.message
    usecase.bot_message_service.unmute_chat_member.assert_not_called()


@pytest.mark.asyncio
async def test_execute_can_moderate_false_returns_error_result(
    usecase: VerifyMemberUseCase,
) -> None:
    """При отсутствии прав модератора возвращается результат с сообщением об ошибке."""
    usecase.bot_permission_service.can_moderate.return_value = False

    result = await usecase.execute(user_tgid="123", chat_tgid="-100123")

    assert result.unmuted is False
    assert "прав" in result.message or "модератор" in result.message
    usecase.chat_service.get_chat.assert_not_called()
    usecase.bot_message_service.unmute_chat_member.assert_not_called()


@pytest.mark.asyncio
async def test_execute_chat_not_found_returns_error_result(
    usecase: VerifyMemberUseCase,
) -> None:
    """При отсутствии чата в БД возвращается результат с сообщением об ошибке."""
    usecase.bot_permission_service.can_moderate.return_value = True
    usecase.chat_service.get_chat.return_value = None

    result = await usecase.execute(user_tgid="123", chat_tgid="-100123")

    assert result.unmuted is False
    assert "чат" in result.message.lower() or "не найден" in result.message.lower()
    usecase.bot_message_service.unmute_chat_member.assert_not_called()
