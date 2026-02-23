"""Тесты для GiveUserWarnUseCase: успех, ModerationError, неуспех apply_punishment, BotBaseException при сохранении."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from constants.punishment import PunishmentActions as Actions
from constants.punishment import PunishmentType
from dto import ModerationActionDTO
from exceptions.moderation import CannotPunishYouSelf
from models.punishment_ladder import PunishmentLadder
from usecases.moderation.give_warn_user import GiveUserWarnUseCase


@pytest.fixture
def dto() -> ModerationActionDTO:
    return ModerationActionDTO(
        action=Actions.WARNING,
        violator_tgid="10",
        violator_username="user",
        admin_username="admin",
        admin_tgid="20",
        chat_tgid="-100",
        chat_title="Chat",
        reply_message_id=1,
        original_message_id=None,
    )


@pytest.fixture
def usecase() -> GiveUserWarnUseCase:
    return GiveUserWarnUseCase(
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
    usecase: GiveUserWarnUseCase, dto: ModerationActionDTO
) -> None:
    """При ModerationError (например CannotPunishYouSelf) отправляется сообщение в ЛС и return."""
    usecase._prepare_moderation_context = AsyncMock(side_effect=CannotPunishYouSelf())

    await usecase.execute(dto=dto)

    usecase.bot_message_service.send_private_message.assert_called_once_with(
        user_tgid="20",
        text=CannotPunishYouSelf().get_user_message(),
    )
    usecase.punishment_service.get_punishment_count.assert_not_called()


@pytest.mark.asyncio
async def test_execute_context_none_returns_early(
    usecase: GiveUserWarnUseCase, dto: ModerationActionDTO
) -> None:
    """Если _prepare_moderation_context вернул None, дальнейшие вызовы не выполняются."""
    usecase._prepare_moderation_context = AsyncMock(return_value=None)

    await usecase.execute(dto=dto)

    usecase.punishment_service.get_punishment_count.assert_not_called()


@pytest.mark.asyncio
async def test_execute_apply_punishment_false_returns_early(
    usecase: GiveUserWarnUseCase, dto: ModerationActionDTO
) -> None:
    """Если apply_punishment вернул False, сохранение в БД не вызывается."""
    context = SimpleNamespace(
        violator=SimpleNamespace(id=1, tg_id="10", username="u"),
        admin=SimpleNamespace(id=2, tg_id="20"),
        chat=SimpleNamespace(id=1, chat_id="-100"),
        dto=dto,
        archive_chat=SimpleNamespace(chat_id="-200"),
    )
    usecase._prepare_moderation_context = AsyncMock(return_value=context)
    usecase.punishment_service.get_punishment_count = AsyncMock(return_value=0)
    usecase.punishment_service.get_punishment = AsyncMock(
        return_value=PunishmentLadder(
            step=1,
            punishment_type=PunishmentType.WARNING,
            duration_seconds=0,
            chat_id=None,
        )
    )
    usecase.bot_message_service.apply_punishment = AsyncMock(return_value=False)

    await usecase.execute(dto=dto)

    usecase.punishment_service.save_punishment_with_status.assert_not_called()


@pytest.mark.asyncio
async def test_execute_save_punishment_exception_returns_early(
    usecase: GiveUserWarnUseCase, dto: ModerationActionDTO
) -> None:
    """При BotBaseException при сохранении наказания _finalize_moderation не вызывается."""
    from exceptions import BotBaseException

    context = SimpleNamespace(
        violator=SimpleNamespace(id=1, tg_id="10", username="u"),
        admin=SimpleNamespace(id=2, tg_id="20"),
        chat=SimpleNamespace(id=1, chat_id="-100"),
        dto=dto,
        archive_chat=SimpleNamespace(chat_id="-200"),
    )
    usecase._prepare_moderation_context = AsyncMock(return_value=context)
    usecase.punishment_service.get_punishment_count = AsyncMock(return_value=0)
    usecase.punishment_service.get_punishment = AsyncMock(
        return_value=PunishmentLadder(
            step=1,
            punishment_type=PunishmentType.WARNING,
            duration_seconds=0,
            chat_id=None,
        )
    )
    usecase.bot_message_service.apply_punishment = AsyncMock(return_value=True)
    usecase.punishment_service.save_punishment_with_status = AsyncMock(
        side_effect=BotBaseException("DB error")
    )
    finalize_mock = AsyncMock()
    usecase._finalize_moderation = finalize_mock

    await usecase.execute(dto=dto)

    finalize_mock.assert_not_called()


@pytest.mark.asyncio
async def test_execute_success_calls_finalize_and_log(
    usecase: GiveUserWarnUseCase, dto: ModerationActionDTO
) -> None:
    """Успешный сценарий: финализация и логирование вызываются."""
    context = SimpleNamespace(
        violator=SimpleNamespace(id=1, tg_id="10", username="u"),
        admin=SimpleNamespace(id=2, tg_id="20"),
        chat=SimpleNamespace(id=1, chat_id="-100", title="Chat"),
        dto=dto,
        archive_chat=SimpleNamespace(chat_id="-200"),
    )
    usecase._prepare_moderation_context = AsyncMock(return_value=context)
    usecase.punishment_service.get_punishment_count = AsyncMock(return_value=0)
    ladder = PunishmentLadder(
        step=1,
        punishment_type=PunishmentType.WARNING,
        duration_seconds=0,
        chat_id=None,
    )
    usecase.punishment_service.get_punishment = AsyncMock(return_value=ladder)
    usecase.bot_message_service.apply_punishment = AsyncMock(return_value=True)
    usecase.punishment_service.save_punishment_with_status = AsyncMock()
    usecase.punishment_service.generate_reason_for_user = lambda **kw: "Причина"
    usecase.punishment_service.generate_report = lambda **kw: "Отчёт"
    usecase._finalize_moderation = AsyncMock()

    await usecase.execute(dto=dto)

    usecase._finalize_moderation.assert_called_once()
    usecase.admin_action_log_service.log_action.assert_called_once()
    assert (
        usecase.admin_action_log_service.log_action.call_args.kwargs[
            "action_type"
        ].value
        == "warn_user"
    )
