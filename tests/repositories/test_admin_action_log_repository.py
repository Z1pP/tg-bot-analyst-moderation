from typing import Any

import pytest

from constants.enums import AdminActionType
from models import AdminActionLog, User
from repositories.admin_action_log_repository import AdminActionLogRepository


@pytest.mark.asyncio
async def test_create_log(db_manager: Any) -> None:
    """Тестирует создание записи в логе действий администратора."""
    # Arrange
    repo = AdminActionLogRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_1", username="admin1")
        session.add(admin)
        await session.commit()
        admin_id = admin.id

    # Act
    action_type = AdminActionType.BAN_USER
    details = "Banned for spam"
    log_entry = await repo.create_log(
        admin_id=admin_id, action_type=action_type, details=details
    )

    # Assert
    assert log_entry.id is not None
    assert log_entry.admin_id == admin_id
    assert log_entry.action_type == action_type.value
    assert log_entry.details == details


@pytest.mark.asyncio
async def test_get_logs_paginated(db_manager: Any) -> None:
    """Тестирует получение всех логов с пагинацией."""
    # Arrange
    repo = AdminActionLogRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_pag", username="admin_pag")
        session.add(admin)
        await session.commit()
        admin_id = admin.id

        # Создаем 15 логов
        for i in range(15):
            log = AdminActionLog(
                admin_id=admin_id,
                action_type=AdminActionType.WARN_USER.value,
                details=f"Log {i}",
            )
            session.add(log)
        await session.commit()

    # Act & Assert
    # Page 1
    logs_p1, total = await repo.get_logs_paginated(page=1, limit=10)

    assert total >= 15
    assert len(logs_p1) == 10

    # Page 2
    logs_p2, total = await repo.get_logs_paginated(page=2, limit=10)
    assert total >= 15
    assert len(logs_p2) >= 5


@pytest.mark.asyncio
async def test_get_logs_by_admin(db_manager: Any) -> None:
    """Тестирует получение логов конкретного администратора."""
    # Arrange
    repo = AdminActionLogRepository(db_manager)
    async with db_manager.session() as session:
        admin_a = User(tg_id="admin_a", username="admin_a")
        admin_b = User(tg_id="admin_b", username="admin_b")
        session.add_all([admin_a, admin_b])
        await session.commit()

        # 5 логов для А
        for i in range(5):
            session.add(
                AdminActionLog(
                    admin_id=admin_a.id, action_type=AdminActionType.BAN_USER.value
                )
            )
        # 3 лога для Б
        for i in range(3):
            session.add(
                AdminActionLog(
                    admin_id=admin_b.id, action_type=AdminActionType.WARN_USER.value
                )
            )
        await session.commit()
        admin_id_a = admin_a.id

    # Act
    logs_a, total_a = await repo.get_logs_by_admin(admin_id=admin_id_a)

    # Assert
    assert total_a == 5
    assert len(logs_a) == 5
    for log in logs_a:
        assert log.admin_id == admin_id_a


@pytest.mark.asyncio
async def test_get_admins_with_logs(db_manager: Any) -> None:
    """Тестирует получение списка администраторов, у которых есть логи."""
    # Arrange
    repo = AdminActionLogRepository(db_manager)
    async with db_manager.session() as session:
        a1 = User(tg_id="a1", username="admin1")
        a2 = User(tg_id="a2", username="admin2")
        a3 = User(tg_id="a3", username="admin3")  # Нет логов
        u1 = User(tg_id="u1", username="user1")  # Не админ, нет логов
        session.add_all([a1, a2, a3, u1])
        await session.commit()

        session.add(
            AdminActionLog(admin_id=a1.id, action_type=AdminActionType.BAN_USER.value)
        )
        session.add(
            AdminActionLog(admin_id=a2.id, action_type=AdminActionType.WARN_USER.value)
        )
        await session.commit()

    # Act
    admins = await repo.get_admins_with_logs()

    # Assert
    # В списке должны быть только те, у кого есть логи (a1 и a2)
    admin_ids = [a[0] for a in admins]
    assert a1.id in admin_ids
    assert a2.id in admin_ids
    assert a3.id not in admin_ids
    assert u1.id not in admin_ids
