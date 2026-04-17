"""Тесты для CancelLastWarnUseCase: нет наказаний для отмены, успех с разбаном, успех без разбана."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from constants.punishment import PunishmentType
from dto import AmnestyUserDTO
from dto.chat_dto import ChatDTO
from services.permissions.bot_permission import ChatMemberStatus
from usecases.amnesty.cancel_last_warn import CancelLastWarnUseCase


@pytest.fixture
def chat_dto() -> ChatDTO:
    return ChatDTO(
        id=1,
        tg_id="-100",
        title="Chat",
        is_antibot_enabled=False,
        is_auto_moderation_enabled=False,
    )


@pytest.fixture
def dto(chat_dto: ChatDTO) -> AmnestyUserDTO:
    return AmnestyUserDTO(
        violator_username="user",
        violator_tgid="10",
        violator_id=1,
        admin_tgid="20",
        admin_username="admin",
        chat_dtos=[chat_dto],
    )


@pytest.fixture
def usecase() -> CancelLastWarnUseCase:
    return CancelLastWarnUseCase(
        bot_message_service=AsyncMock(),
        bot_permission_service=AsyncMock(),
        punishment_repository=AsyncMock(),
        punishment_ladder_repository=AsyncMock(),
        user_chat_status_repository=AsyncMock(),
        chat_service=AsyncMock(),
        admin_action_log_service=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_execute_no_punishment_to_cancel_returns_failure_dto(
    usecase: CancelLastWarnUseCase, dto: AmnestyUserDTO
) -> None:
    """Если нет наказаний для отмены — возвращается CancelWarnResultDTO(success=False)."""
    archive_chat = SimpleNamespace(chat_id="-200")
    usecase._validate_and_get_archive_chats = AsyncMock(return_value=[archive_chat])
    usecase.bot_permission_service.get_chat_member_status = AsyncMock(
        return_value=ChatMemberStatus(is_banned=False)
    )
    usecase.punishment_repository.delete_last_punishment = AsyncMock(return_value=False)

    result = await usecase.execute(dto=dto)

    assert result.success is False
    assert result.current_warns_count == 0
    usecase.bot_message_service.send_chat_message.assert_not_called()


@pytest.mark.asyncio
async def test_execute_success_updates_status_and_sends_report(
    usecase: CancelLastWarnUseCase, dto: AmnestyUserDTO
) -> None:
    """Успешная отмена: обновление статуса, отправка отчёта в архив, логирование."""
    archive_chat = SimpleNamespace(chat_id="-200")
    usecase._validate_and_get_archive_chats = AsyncMock(return_value=[archive_chat])
    usecase.bot_permission_service.get_chat_member_status = AsyncMock(
        return_value=ChatMemberStatus(is_banned=False)
    )
    usecase.punishment_repository.delete_last_punishment = AsyncMock(return_value=True)
    usecase.punishment_repository.count_punishments = AsyncMock(return_value=0)
    usecase.punishment_ladder_repository.get_punishment_by_step = AsyncMock(
        return_value=SimpleNamespace(
            punishment_type=PunishmentType.WARNING,
            duration_seconds=None,
        )
    )
    usecase._send_report_to_archives = AsyncMock()

    result = await usecase.execute(dto=dto)

    assert result.success is True
    assert result.current_warns_count == 0
    usecase._send_report_to_archives.assert_called_once()
    usecase.admin_action_log_service.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_execute_success_user_banned_unbans_and_updates_status(
    usecase: CancelLastWarnUseCase, dto: AmnestyUserDTO
) -> None:
    """Если после отмены варнов count=0 и пользователь забанен — вызывается unban."""
    archive_chat = SimpleNamespace(chat_id="-200")
    usecase._validate_and_get_archive_chats = AsyncMock(return_value=[archive_chat])
    member_status = ChatMemberStatus(is_banned=True, banned_until=None)
    usecase.bot_permission_service.get_chat_member_status = AsyncMock(
        return_value=member_status
    )
    usecase.punishment_repository.delete_last_punishment = AsyncMock(return_value=True)
    usecase.punishment_repository.count_punishments = AsyncMock(return_value=0)
    usecase.bot_message_service.unban_chat_member = AsyncMock(return_value=True)
    usecase.punishment_ladder_repository.get_punishment_by_step = AsyncMock(
        return_value=SimpleNamespace(
            punishment_type=PunishmentType.WARNING,
            duration_seconds=None,
        )
    )
    usecase._send_report_to_archives = AsyncMock()

    result = await usecase.execute(dto=dto)

    assert result.success is True
    usecase.bot_message_service.unban_chat_member.assert_called_once_with(
        chat_tg_id="-100", user_tg_id=10
    )
