"""Тесты для ReportScheduleRepository."""

from datetime import datetime, time, timezone
from typing import Any

import pytest

from models import ChatSession, ReportSchedule
from repositories.report_schedule_repository import ReportScheduleRepository


@pytest.mark.asyncio
async def test_create_schedule(db_manager: Any) -> None:
    """Создание расписания."""
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_rs", title="RS Chat")
        session.add(chat)
        await session.commit()
        chat_id = chat.id

    repo = ReportScheduleRepository(db_manager)
    schedule = await repo.create_schedule(
        chat_id=chat_id,
        tz_name="Europe/Moscow",
        sent_time=time(10, 0),
        enabled=True,
    )
    assert schedule.id is not None
    assert schedule.chat_id == chat_id
    assert schedule.timezone == "Europe/Moscow"
    assert schedule.sent_time == time(10, 0)
    assert schedule.enabled is True
    assert schedule.next_run_at is not None


@pytest.mark.asyncio
async def test_get_schedule(db_manager: Any) -> None:
    """Получение расписания по chat_id."""
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_rs_get", title="RS Get")
        session.add(chat)
        await session.flush()
        s = ReportSchedule(
            chat_id=chat.id,
            timezone="Europe/Moscow",
            sent_time=time(12, 0),
            enabled=True,
            next_run_at=datetime.now(timezone.utc),
        )
        session.add(s)
        await session.commit()
        chat_id = chat.id

    repo = ReportScheduleRepository(db_manager)
    found = await repo.get_schedule(chat_id)
    assert found is not None
    assert found.sent_time == time(12, 0)


@pytest.mark.asyncio
async def test_get_schedule_not_found(db_manager: Any) -> None:
    """get_schedule возвращает None для чата без расписания."""
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_rs_nf", title="RS NF")
        session.add(chat)
        await session.commit()
        chat_id = chat.id

    repo = ReportScheduleRepository(db_manager)
    assert await repo.get_schedule(chat_id) is None


@pytest.mark.asyncio
async def test_update_schedule(db_manager: Any) -> None:
    """Обновление расписания."""
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_rs_upd", title="RS Upd")
        session.add(chat)
        await session.flush()
        s = ReportSchedule(
            chat_id=chat.id,
            timezone="Europe/Moscow",
            sent_time=time(9, 0),
            enabled=True,
            next_run_at=datetime.now(timezone.utc),
        )
        session.add(s)
        await session.commit()
        schedule_id = s.id

    repo = ReportScheduleRepository(db_manager)
    updated = await repo.update_schedule(
        schedule_id, sent_time=time(14, 30), enabled=True
    )
    assert updated is not None
    assert updated.sent_time == time(14, 30)


@pytest.mark.asyncio
async def test_update_schedule_disable(db_manager: Any) -> None:
    """Отключение расписания обнуляет next_run_at."""
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_rs_dis", title="RS Dis")
        session.add(chat)
        await session.flush()
        s = ReportSchedule(
            chat_id=chat.id,
            timezone="Europe/Moscow",
            sent_time=time(10, 0),
            enabled=True,
            next_run_at=datetime.now(timezone.utc),
        )
        session.add(s)
        await session.commit()
        schedule_id = s.id

    repo = ReportScheduleRepository(db_manager)
    updated = await repo.update_schedule(schedule_id, enabled=False)
    assert updated is not None
    assert updated.enabled is False
    assert updated.next_run_at is None


@pytest.mark.asyncio
async def test_update_schedule_not_found(db_manager: Any) -> None:
    """update_schedule возвращает None для несуществующего id."""
    repo = ReportScheduleRepository(db_manager)
    assert await repo.update_schedule(99999, enabled=False) is None


def test_calculate_next_run_today_future(db_manager: Any) -> None:
    """_calculate_next_run: если время отправки ещё не прошло сегодня — следующее сегодня."""
    from types import SimpleNamespace

    repo = ReportScheduleRepository(db_manager)
    schedule = SimpleNamespace(
        id=1,
        timezone="Europe/Moscow",
        sent_time=time(23, 0),
    )
    now_utc = datetime(2025, 2, 20, 19, 0, tzinfo=timezone.utc)
    next_run = repo._calculate_next_run(schedule, now_utc)
    assert next_run > now_utc
    assert (next_run - now_utc).total_seconds() >= 120


def test_calculate_next_run_already_passed(db_manager: Any) -> None:
    """_calculate_next_run: если время прошло — следующее завтра."""
    from types import SimpleNamespace

    repo = ReportScheduleRepository(db_manager)
    schedule = SimpleNamespace(
        id=1,
        timezone="UTC",
        sent_time=time(10, 0),
    )
    now_utc = datetime(2025, 2, 20, 12, 0, tzinfo=timezone.utc)
    next_run = repo._calculate_next_run(schedule, now_utc)
    assert next_run > now_utc
    assert next_run.day >= 20
