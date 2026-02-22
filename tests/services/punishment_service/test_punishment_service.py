"""Тесты для PunishmentService."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from constants.punishment import PunishmentType
from dto import ModerationActionDTO
from models.punishment_ladder import PunishmentLadder
from repositories import PunishmentLadderRepository, PunishmentRepository
from repositories.user_chat_status_repository import UserChatStatusRepository
from services.punishment_service import PunishmentService


@pytest.fixture
def mock_punishment_repo() -> AsyncMock:
    return AsyncMock(spec=PunishmentRepository)


@pytest.fixture
def mock_ladder_repo() -> AsyncMock:
    return AsyncMock(spec=PunishmentLadderRepository)


@pytest.fixture
def mock_status_repo() -> AsyncMock:
    return AsyncMock(spec=UserChatStatusRepository)


@pytest.fixture
def service(
    mock_punishment_repo: AsyncMock,
    mock_ladder_repo: AsyncMock,
    mock_status_repo: AsyncMock,
) -> PunishmentService:
    return PunishmentService(
        punishment_repository=mock_punishment_repo,
        punishment_ladder_repository=mock_ladder_repo,
        user_chat_status_repository=mock_status_repo,
    )


def test_generate_reason_for_user_warning(service: PunishmentService) -> None:
    """Генерация текста для предупреждения."""
    text = service.generate_reason_for_user(
        duration_of_punishment=0,
        violator_username="user",
        violator_tg_id="123",
        punishment_type=PunishmentType.WARNING,
    )
    assert "@user" in text or "user" in text
    assert len(text) > 10


def test_generate_reason_for_user_mute(service: PunishmentService) -> None:
    """Генерация текста для мута с длительностью."""
    text = service.generate_reason_for_user(
        duration_of_punishment=3600,
        violator_username=None,
        violator_tg_id="456",
        punishment_type=PunishmentType.MUTE,
    )
    assert "ID:456" in text or "456" in text
    assert "1" in text or "час" in text.lower() or "hour" in text.lower()


def test_generate_reason_for_user_ban(service: PunishmentService) -> None:
    """Генерация текста для бана."""
    text = service.generate_reason_for_user(
        duration_of_punishment=0,
        violator_username="banned",
        violator_tg_id="789",
        punishment_type=PunishmentType.BAN,
    )
    assert "banned" in text or "789" in text


@pytest.mark.asyncio
async def test_get_punishment_count(
    service: PunishmentService, mock_punishment_repo: AsyncMock
) -> None:
    mock_punishment_repo.count_punishments.return_value = 2
    result = await service.get_punishment_count(user_id=1, chat_id=10)
    assert result == 2
    mock_punishment_repo.count_punishments.assert_called_once_with(
        user_id=1, chat_id=10
    )


@pytest.mark.asyncio
async def test_get_punishment_returns_ladder_step(
    service: PunishmentService, mock_ladder_repo: AsyncMock
) -> None:
    ladder_step = PunishmentLadder(
        step=1,
        punishment_type=PunishmentType.WARNING,
        duration_seconds=0,
        chat_id=None,
    )
    mock_ladder_repo.get_ladder_by_chat_id.return_value = [
        ladder_step,
    ]
    mock_ladder_repo.get_punishment_by_step.return_value = ladder_step

    result = await service.get_punishment(warn_count=0, chat_id="-100")
    assert result.step == 1
    assert result.punishment_type == PunishmentType.WARNING


@pytest.mark.asyncio
async def test_get_punishment_returns_default_when_no_ladder(
    service: PunishmentService, mock_ladder_repo: AsyncMock
) -> None:
    mock_ladder_repo.get_ladder_by_chat_id.return_value = None
    mock_ladder_repo.get_global_ladder.return_value = None
    mock_ladder_repo.get_punishment_by_step.return_value = None

    result = await service.get_punishment(warn_count=0, chat_id="-100")
    assert result.step == 1
    assert result.punishment_type == PunishmentType.WARNING
    assert result.duration_seconds == 0


def test_format_ladder_text_empty(service: PunishmentService) -> None:
    """Пустая лестница — возвращается текст пустого списка."""
    text = service.format_ladder_text([])
    assert len(text) > 0
    assert "пуст" in text.lower() or "empty" in text.lower() or "нет" in text.lower()


def test_format_ladder_text_with_steps(service: PunishmentService) -> None:
    """Лестница с шагами форматируется в текст."""
    ladder = [
        PunishmentLadder(
            step=1,
            punishment_type=PunishmentType.WARNING,
            duration_seconds=0,
            chat_id=None,
        ),
        PunishmentLadder(
            step=2,
            punishment_type=PunishmentType.MUTE,
            duration_seconds=3600,
            chat_id=None,
        ),
    ]
    text = service.format_ladder_text(ladder)
    assert "1" in text and "2" in text
    assert "Предупреждение" in text or "предупреждение" in text
    assert "Ограничение" in text or "ограничение" in text


def test_generate_ban_report(service: PunishmentService) -> None:
    """Генерация отчёта о бане."""
    from constants.punishment import PunishmentActions as Actions

    dto = ModerationActionDTO(
        action=Actions.WARNING,
        violator_tgid="123",
        violator_username="user",
        admin_username="admin",
        admin_tgid="1",
        chat_tgid="-100",
        chat_title="Chat",
        reply_message_id=1,
        original_message_id=2,
    )
    date = datetime.now(timezone.utc)
    report = service.generate_ban_report(dto, date=date)
    assert "user" in report or "123" in report
    assert "admin" in report
    assert "Chat" in report
