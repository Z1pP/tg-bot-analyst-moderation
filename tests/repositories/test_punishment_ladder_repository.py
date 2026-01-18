from typing import Any

import pytest

from constants.punishment import PunishmentType
from models.punishment_ladder import PunishmentLadder
from repositories.punishment_ladder_repository import PunishmentLadderRepository


@pytest.fixture(autouse=True)
async def cleanup(db_manager: Any):
    """Очистка таблицы перед каждым тестом."""
    async with db_manager.session() as session:
        from sqlalchemy import delete

        await session.execute(delete(PunishmentLadder))
        await session.commit()


@pytest.mark.asyncio
async def test_create_ladder(db_manager: Any) -> None:
    """
    Тестирует создание лестницы наказаний.
    """
    # Arrange
    repo = PunishmentLadderRepository(db_manager)
    steps = [
        PunishmentLadder(step=1, punishment_type=PunishmentType.WARNING, chat_id=None),
        PunishmentLadder(
            step=2,
            punishment_type=PunishmentType.MUTE,
            duration_seconds=3600,
            chat_id="12345",
        ),
    ]

    # Act
    await repo.create_ladder(steps)

    # Assert
    async with db_manager.session() as session:
        from sqlalchemy import select

        result = await session.execute(select(PunishmentLadder))
        saved_steps = result.scalars().all()
        assert len(saved_steps) == 2

        step1 = next(s for s in saved_steps if s.step == 1)
        assert step1.punishment_type == PunishmentType.WARNING
        assert step1.chat_id is None

        step2 = next(s for s in saved_steps if s.step == 2)
        assert step2.punishment_type == PunishmentType.MUTE
        assert step2.duration_seconds == 3600
        assert step2.chat_id == "12345"


@pytest.mark.asyncio
async def test_get_punishment_by_step_priority(db_manager: Any) -> None:
    """
    Тестирует приоритетность получения наказания (чат-специфичное выше глобального).
    """
    # Arrange
    repo = PunishmentLadderRepository(db_manager)
    chat_id = "test_chat"
    step = 1

    global_punishment = PunishmentLadder(
        step=step, punishment_type=PunishmentType.WARNING, chat_id=None
    )
    chat_punishment = PunishmentLadder(
        step=step, punishment_type=PunishmentType.MUTE, chat_id=chat_id
    )

    await repo.create_ladder([global_punishment, chat_punishment])

    # Act
    result = await repo.get_punishment_by_step(step=step, chat_id=chat_id)

    # Assert
    assert result is not None
    assert result.punishment_type == PunishmentType.MUTE
    assert result.chat_id == chat_id


@pytest.mark.asyncio
async def test_get_punishment_by_step_fallback(db_manager: Any) -> None:
    """
    Тестирует fallback на глобальное наказание, если для чата не задано.
    """
    # Arrange
    repo = PunishmentLadderRepository(db_manager)
    chat_id = "other_chat"
    step = 1

    global_punishment = PunishmentLadder(
        step=step, punishment_type=PunishmentType.WARNING, chat_id=None
    )

    await repo.create_ladder([global_punishment])

    # Act
    result = await repo.get_punishment_by_step(step=step, chat_id=chat_id)

    # Assert
    assert result is not None
    assert result.punishment_type == PunishmentType.WARNING
    assert result.chat_id is None


@pytest.mark.asyncio
async def test_get_punishment_by_step_not_found(db_manager: Any) -> None:
    """
    Тестирует возврат None, если наказание не найдено.
    """
    # Arrange
    repo = PunishmentLadderRepository(db_manager)

    # Act
    result = await repo.get_punishment_by_step(step=1, chat_id="any")

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_ladder_by_chat_id(db_manager: Any) -> None:
    """
    Тестирует получение всей лестницы для чата.
    """
    # Arrange
    repo = PunishmentLadderRepository(db_manager)
    chat_id = "ladder_chat"
    steps = [
        PunishmentLadder(step=2, punishment_type=PunishmentType.MUTE, chat_id=chat_id),
        PunishmentLadder(
            step=1, punishment_type=PunishmentType.WARNING, chat_id=chat_id
        ),
        PunishmentLadder(step=1, punishment_type=PunishmentType.BAN, chat_id="other"),
    ]
    await repo.create_ladder(steps)

    # Act
    ladder = await repo.get_ladder_by_chat_id(chat_id)

    # Assert
    assert len(ladder) == 2
    assert ladder[0].step == 1
    assert ladder[1].step == 2
    assert all(s.chat_id == chat_id for s in ladder)


@pytest.mark.asyncio
async def test_get_global_ladder(db_manager: Any) -> None:
    """
    Тестирует получение глобальной лестницы.
    """
    # Arrange
    repo = PunishmentLadderRepository(db_manager)
    steps = [
        PunishmentLadder(step=2, punishment_type=PunishmentType.BAN, chat_id=None),
        PunishmentLadder(step=1, punishment_type=PunishmentType.WARNING, chat_id=None),
        PunishmentLadder(
            step=1, punishment_type=PunishmentType.MUTE, chat_id="specific"
        ),
    ]
    await repo.create_ladder(steps)

    # Act
    ladder = await repo.get_global_ladder()

    # Assert
    assert len(ladder) == 2
    assert ladder[0].step == 1
    assert ladder[1].step == 2
    assert all(s.chat_id is None for s in ladder)


@pytest.mark.asyncio
async def test_delete_ladder_by_chat_id(db_manager: Any) -> None:
    """
    Тестирует удаление лестницы чата.
    """
    # Arrange
    repo = PunishmentLadderRepository(db_manager)
    chat_id = "to_delete"
    steps = [
        PunishmentLadder(
            step=1, punishment_type=PunishmentType.WARNING, chat_id=chat_id
        ),
        PunishmentLadder(step=1, punishment_type=PunishmentType.WARNING, chat_id=None),
        PunishmentLadder(
            step=1, punishment_type=PunishmentType.WARNING, chat_id="stay"
        ),
    ]
    await repo.create_ladder(steps)

    # Act
    await repo.delete_ladder_by_chat_id(chat_id)

    # Assert
    async with db_manager.session() as session:
        from sqlalchemy import select

        result = await session.execute(select(PunishmentLadder))
        remaining = result.scalars().all()
        assert len(remaining) == 2
        assert all(s.chat_id != chat_id for s in remaining)
