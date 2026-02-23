"""Тесты для GiveUserBanUseCase: ModerationError, apply_punishment False, BotBaseException при update_status, успех."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from constants.punishment import PunishmentActions as Actions
from dto import ModerationActionDTO
from exceptions import BotBaseException
from exceptions.moderation import CannotPunishChatAdminError
from usecases.moderation.give_ban_user import GiveUserBanUseCase


@pytest.fixture
def dto() -> ModerationActionDTO:
    return ModerationActionDTO(
        action=Actions.BAN,
        violator_tgid="10",
        violator_username="user",
        admin_username="admin",
        admin_tgid="20",
        chat_tgid="-100",
        chat_title="Chat",
    )


@pytest.fixture
def usecase() -> GiveUserBanUseCase:
    return GiveUserBanUseCase(
        user_service=AsyncMock(),
        bot_message_service=AsyncMock(),
        chat_service=AsyncMock(),
        punishment_service=AsyncMock(),
        user_chat_status_repository=AsyncMock(),
        permission_service=AsyncMock(),
        admin_action_log_service=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_execute_moderation_error_sends_private_message(
    usecase: GiveUserBanUseCase, dto: ModerationActionDTO
) -> None:
    """При ModerationError отправляется сообщение в ЛС."""
    usecase._prepare_moderation_context = AsyncMock(
        side_effect=CannotPunishChatAdminError()
    )

    await usecase.execute(dto=dto)

    usecase.bot_message_service.send_private_message.assert_called_once_with(
        user_tgid="20",
        text=CannotPunishChatAdminError().get_user_message(),
    )


@pytest.mark.asyncio
async def test_execute_apply_punishment_false_returns_early(
    usecase: GiveUserBanUseCase, dto: ModerationActionDTO
) -> None:
    """Если apply_punishment вернул False, update_status не вызывается."""
    context = SimpleNamespace(
        violator=SimpleNamespace(id=1, tg_id="10"),
        admin=SimpleNamespace(id=2, tg_id="20"),
        chat=SimpleNamespace(id=1, chat_id="-100"),
        dto=dto,
        archive_chat=SimpleNamespace(chat_id="-200"),
    )
    usecase._prepare_moderation_context = AsyncMock(return_value=context)
    usecase.bot_message_service.apply_punishment = AsyncMock(return_value=False)

    await usecase.execute(dto=dto)

    usecase.user_chat_status_repository.update_status.assert_not_called()


@pytest.mark.asyncio
async def test_execute_update_status_exception_returns_early(
    usecase: GiveUserBanUseCase, dto: ModerationActionDTO
) -> None:
    """При BotBaseException при update_status финализация не вызывается."""
    context = SimpleNamespace(
        violator=SimpleNamespace(id=1, tg_id="10"),
        admin=SimpleNamespace(id=2, tg_id="20"),
        chat=SimpleNamespace(id=1, chat_id="-100"),
        dto=dto,
        archive_chat=SimpleNamespace(chat_id="-200"),
    )
    usecase._prepare_moderation_context = AsyncMock(return_value=context)
    usecase.bot_message_service.apply_punishment = AsyncMock(return_value=True)
    usecase.user_chat_status_repository.update_status = AsyncMock(
        side_effect=BotBaseException("DB error")
    )
    finalize_mock = AsyncMock()
    usecase._finalize_moderation = finalize_mock

    await usecase.execute(dto=dto)

    finalize_mock.assert_not_called()


@pytest.mark.asyncio
async def test_execute_success_calls_finalize_and_log(
    usecase: GiveUserBanUseCase, dto: ModerationActionDTO
) -> None:
    """Успешный бан: финализация и логирование вызываются."""
    context = SimpleNamespace(
        violator=SimpleNamespace(id=1, tg_id="10"),
        admin=SimpleNamespace(id=2, tg_id="20"),
        chat=SimpleNamespace(id=1, chat_id="-100", title="Chat"),
        dto=dto,
        archive_chat=SimpleNamespace(chat_id="-200"),
    )
    usecase._prepare_moderation_context = AsyncMock(return_value=context)
    usecase.bot_message_service.apply_punishment = AsyncMock(return_value=True)
    usecase.user_chat_status_repository.update_status = AsyncMock()
    usecase.punishment_service.generate_ban_report = lambda **kw: "Отчёт о бане"
    usecase.punishment_service.generate_reason_for_user = lambda **kw: "Забанен"
    usecase._finalize_moderation = AsyncMock()

    await usecase.execute(dto=dto)

    usecase._finalize_moderation.assert_called_once()
    usecase.admin_action_log_service.log_action.assert_called_once()
