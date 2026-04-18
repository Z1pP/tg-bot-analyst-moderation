"""Тесты для UnmuteUserUseCase: отправка отчёта в архив и логирование."""

from types import SimpleNamespace
from unittest.mock import AsyncMock

import pytest

from dto import AmnestyUserDTO
from dto.chat_dto import ChatDTO
from usecases.amnesty.unmute_user import UnmuteUserUseCase


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
def usecase() -> UnmuteUserUseCase:
    return UnmuteUserUseCase(
        bot_message_service=AsyncMock(),
        bot_permission_service=AsyncMock(),
        user_chat_status_repository=AsyncMock(),
        chat_service=AsyncMock(),
        admin_action_log_service=AsyncMock(),
    )


@pytest.mark.asyncio
async def test_execute_sends_report_and_logs(
    usecase: UnmuteUserUseCase, dto: AmnestyUserDTO
) -> None:
    """Успешный размут: отчёт в архив, обновление статуса, логирование."""
    archive_chat = SimpleNamespace(chat_id="-200")
    usecase._validate_and_get_archive_chats = AsyncMock(return_value=[archive_chat])
    usecase.bot_permission_service.get_chat_member_status = AsyncMock(
        return_value=SimpleNamespace(is_muted=False)
    )
    usecase._send_report_to_archives = AsyncMock()

    await usecase.execute(dto=dto)

    usecase._send_report_to_archives.assert_called_once()
    call_args = usecase._send_report_to_archives.call_args[0]
    assert "Размут" in call_args[1]
    usecase.admin_action_log_service.log_action.assert_called_once()


@pytest.mark.asyncio
async def test_execute_when_muted_calls_unmute(
    usecase: UnmuteUserUseCase, dto: AmnestyUserDTO
) -> None:
    """Если пользователь замучен — вызывается unmute_chat_member."""
    archive_chat = SimpleNamespace(chat_id="-200")
    usecase._validate_and_get_archive_chats = AsyncMock(return_value=[archive_chat])
    usecase.bot_permission_service.get_chat_member_status = AsyncMock(
        return_value=SimpleNamespace(is_muted=True)
    )
    usecase._send_report_to_archives = AsyncMock()

    await usecase.execute(dto=dto)

    usecase.bot_message_service.unmute_chat_member.assert_called_once_with(
        chat_tg_id="-100",
        user_tg_id=10,
    )
