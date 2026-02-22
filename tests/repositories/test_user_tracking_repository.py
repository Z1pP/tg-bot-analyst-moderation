"""Тесты для UserTrackingRepository."""

from typing import Any

import pytest

from models import User
from repositories.user_tracking_repository import UserTrackingRepository


@pytest.mark.asyncio
async def test_add_user_to_tracking(db_manager: Any) -> None:
    """Добавление пользователя в отслеживание админа."""
    repo = UserTrackingRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_tr_add", username="admin_add")
        user = User(tg_id="user_tr_add", username="user_add")
        session.add_all([admin, user])
        await session.commit()
        admin_id, user_id = admin.id, user.id

    await repo.add_user_to_tracking(admin_id=admin_id, user_id=user_id)

    tracked = await repo.get_tracked_users_by_admin("admin_tr_add")
    assert len(tracked) == 1
    assert tracked[0].username == "user_add"


@pytest.mark.asyncio
async def test_remove_user_from_tracking(db_manager: Any) -> None:
    """Удаление пользователя из отслеживания."""
    repo = UserTrackingRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_tr_rem", username="admin_rem")
        user = User(tg_id="user_tr_rem", username="user_rem")
        session.add_all([admin, user])
        await session.commit()
        admin_id, user_id = admin.id, user.id

    await repo.add_user_to_tracking(admin_id=admin_id, user_id=user_id)
    await repo.remove_user_from_tracking(admin_id=admin_id, user_id=user_id)

    tracked = await repo.get_tracked_users_by_admin("admin_tr_rem")
    assert len(tracked) == 0


@pytest.mark.asyncio
async def test_get_tracked_users_by_admin_empty(db_manager: Any) -> None:
    """Пустой список для админа без отслеживаемых."""
    repo = UserTrackingRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_tr_empty", username="admin_empty")
        session.add(admin)
        await session.commit()

    result = await repo.get_tracked_users_by_admin("admin_tr_empty")
    assert result == []


@pytest.mark.asyncio
async def test_get_tracked_users_by_admin_unknown(db_manager: Any) -> None:
    """Пустой список для неизвестного tg_id админа."""
    repo = UserTrackingRepository(db_manager)
    result = await repo.get_tracked_users_by_admin("unknown_tg_id_999")
    assert result == []


@pytest.mark.asyncio
async def test_has_tracked_users_true(db_manager: Any) -> None:
    """has_tracked_users возвращает True при наличии отслеживаемых."""
    repo = UserTrackingRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_has_1", username="admin_has")
        user = User(tg_id="user_has_1", username="user_has")
        session.add_all([admin, user])
        await session.commit()
        admin_id, user_id = admin.id, user.id

    await repo.add_user_to_tracking(admin_id=admin_id, user_id=user_id)
    assert await repo.has_tracked_users("admin_has_1") is True


@pytest.mark.asyncio
async def test_has_tracked_users_false(db_manager: Any) -> None:
    """has_tracked_users возвращает False при отсутствии отслеживаемых."""
    repo = UserTrackingRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_has_0", username="admin_has0")
        session.add(admin)
        await session.commit()

    assert await repo.has_tracked_users("admin_has_0") is False


@pytest.mark.asyncio
async def test_get_tracked_users_with_dates(db_manager: Any) -> None:
    """Получение отслеживаемых с датами добавления."""
    repo = UserTrackingRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_dates", username="admin_dates")
        user = User(tg_id="user_dates", username="user_dates")
        session.add_all([admin, user])
        await session.commit()
        admin_id, user_id = admin.id, user.id

    await repo.add_user_to_tracking(admin_id=admin_id, user_id=user_id)
    result = await repo.get_tracked_users_with_dates("admin_dates")
    assert len(result) == 1
    u, created_at = result[0]
    assert u.username == "user_dates"
    assert created_at is not None


@pytest.mark.asyncio
async def test_delete_all_tracked_users_for_admin(db_manager: Any) -> None:
    """Удаление всех отслеживаемых для админа."""
    repo = UserTrackingRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_del_all", username="admin_del")
        u1 = User(tg_id="u1_del_all", username="u1_del")
        u2 = User(tg_id="u2_del_all", username="u2_del")
        session.add_all([admin, u1, u2])
        await session.commit()
        admin_id, uid1, uid2 = admin.id, u1.id, u2.id

    await repo.add_user_to_tracking(admin_id=admin_id, user_id=uid1)
    await repo.add_user_to_tracking(admin_id=admin_id, user_id=uid2)
    count = await repo.delete_all_tracked_users_for_admin(admin_id)
    assert count == 2
    assert await repo.has_tracked_users("admin_del_all") is False
