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
    mock_punishment_repo.count_punishments = AsyncMock(return_value=2)
    result = await service.get_punishment_count(user_id=1, chat_id=10)
    assert result == 2
    mock_punishment_repo.count_punishments.assert_called_once_with(
        user_id=1, chat_id=10
    )


@pytest.mark.asyncio
async def test_get_punishment_count_without_chat_id(
    service: PunishmentService, mock_punishment_repo: AsyncMock
) -> None:
    """get_punishment_count без chat_id вызывает count_punishments с chat_id=None."""
    mock_punishment_repo.count_punishments = AsyncMock(return_value=5)
    result = await service.get_punishment_count(user_id=1, chat_id=None)
    assert result == 5
    mock_punishment_repo.count_punishments.assert_called_once_with(
        user_id=1, chat_id=None
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


def test_generate_report(service: PunishmentService) -> None:
    """Генерация отчёта о наказании (warn/mute) через _format_report_body."""
    from constants.punishment import PunishmentActions as Actions

    dto = ModerationActionDTO(
        action=Actions.WARNING,
        violator_tgid="123",
        violator_username="user",
        admin_username="admin",
        admin_tgid="1",
        chat_tgid="-100",
        chat_title="Chat",
        reason="Спам",
    )
    date = datetime.now(timezone.utc)
    ladder = PunishmentLadder(
        step=1,
        punishment_type=PunishmentType.MUTE,
        duration_seconds=3600,
        chat_id=None,
    )
    report = service.generate_report(
        dto=dto,
        punishment_ladder=ladder,
        date=date,
        message_deleted=True,
    )
    assert "user" in report or "123" in report
    assert "admin" in report
    assert "Chat" in report
    assert "Спам" in report


@pytest.mark.asyncio
async def test_get_max_punishment_from_chat(
    service: PunishmentService, mock_ladder_repo: AsyncMock
) -> None:
    """get_max_punishment возвращает последний шаг лестницы чата."""
    max_step = PunishmentLadder(
        step=3,
        punishment_type=PunishmentType.BAN,
        duration_seconds=None,
        chat_id="-100",
    )
    mock_ladder_repo.get_ladder_by_chat_id.return_value = [
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
        max_step,
    ]
    result = await service.get_max_punishment(chat_id="-100")
    assert result == max_step


@pytest.mark.asyncio
async def test_get_max_punishment_from_global(
    service: PunishmentService, mock_ladder_repo: AsyncMock
) -> None:
    """get_max_punishment при отсутствии лестницы чата использует глобальную."""
    mock_ladder_repo.get_ladder_by_chat_id.return_value = None
    global_step = PunishmentLadder(
        step=2,
        punishment_type=PunishmentType.BAN,
        duration_seconds=None,
        chat_id=None,
    )
    mock_ladder_repo.get_global_ladder.return_value = [global_step]
    result = await service.get_max_punishment(chat_id="-100")
    assert result == global_step


@pytest.mark.asyncio
async def test_get_max_punishment_returns_none(
    service: PunishmentService, mock_ladder_repo: AsyncMock
) -> None:
    """get_max_punishment при отсутствии и чатовой, и глобальной лестницы возвращает None."""
    mock_ladder_repo.get_ladder_by_chat_id.return_value = None
    mock_ladder_repo.get_global_ladder.return_value = None

    result = await service.get_max_punishment(chat_id="-100")

    assert result is None


@pytest.mark.asyncio
async def test_create_punishment(
    service: PunishmentService,
    mock_punishment_repo: AsyncMock,
) -> None:
    """create_punishment создаёт запись через репозиторий."""
    from models import User

    user = User(id=1, tg_id="10", username="u", role=None)
    ladder = PunishmentLadder(
        step=1,
        punishment_type=PunishmentType.WARNING,
        duration_seconds=0,
        chat_id=None,
    )
    created = type("Punishment", (), {"id": 1})()
    mock_punishment_repo.create_punishment = AsyncMock(return_value=created)
    result = await service.create_punishment(
        user=user,
        punishment=ladder,
        admin_id=2,
        chat_id=1,
    )
    assert result == created
    mock_punishment_repo.create_punishment.assert_called_once()


@pytest.mark.asyncio
async def test_save_punishment_with_status_mute(
    service: PunishmentService,
    mock_punishment_repo: AsyncMock,
    mock_status_repo: AsyncMock,
) -> None:
    """save_punishment_with_status при MUTE создаёт наказание и обновляет muted_until."""
    from models import User

    user = User(id=1, tg_id="10", username="u", role=None)
    ladder = PunishmentLadder(
        step=1,
        punishment_type=PunishmentType.MUTE,
        duration_seconds=3600,
        chat_id=None,
    )
    mock_punishment_repo.create_punishment = AsyncMock(return_value=None)
    await service.save_punishment_with_status(
        user=user,
        punishment=ladder,
        admin_id=2,
        chat_id=1,
    )
    mock_status_repo.update_status.assert_called_once()
    call_kw = mock_status_repo.update_status.call_args.kwargs
    assert call_kw.get("is_muted") is True


@pytest.mark.asyncio
async def test_save_punishment_with_status_ban(
    service: PunishmentService,
    mock_punishment_repo: AsyncMock,
    mock_status_repo: AsyncMock,
) -> None:
    """save_punishment_with_status при BAN обновляет is_banned."""
    from models import User

    user = User(id=1, tg_id="10", username="u", role=None)
    ladder = PunishmentLadder(
        step=2,
        punishment_type=PunishmentType.BAN,
        duration_seconds=None,
        chat_id=None,
    )
    mock_punishment_repo.create_punishment = AsyncMock(return_value=None)
    await service.save_punishment_with_status(
        user=user,
        punishment=ladder,
        admin_id=2,
        chat_id=1,
    )
    call_kw = mock_status_repo.update_status.call_args.kwargs
    assert call_kw.get("is_banned") is True


@pytest.mark.asyncio
async def test_delete_user_punishments(
    service: PunishmentService, mock_punishment_repo: AsyncMock
) -> None:
    """delete_user_punishments вызывает репозиторий и возвращает количество."""
    mock_punishment_repo.delete_user_punishments = AsyncMock(return_value=2)
    result = await service.delete_user_punishments(user_id=1, chat_id=10)
    assert result == 2
    mock_punishment_repo.delete_user_punishments.assert_called_once_with(1, 10)
