from typing import Any

import pytest

from models import AdminChatAccess, ChatSession, User
from repositories.chat_tracking_repository import ChatTrackingRepository


@pytest.mark.asyncio
async def test_add_chat_to_tracking(db_manager: Any) -> None:
    """Тестирует добавление чата в отслеживание для администратора."""
    # Arrange
    repo = ChatTrackingRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_track", username="admin_track")
        chat = ChatSession(chat_id="-100_track", title="Tracked Chat")
        session.add_all([admin, chat])
        await session.commit()
        admin_id, chat_id = admin.id, chat.id

    # Act
    access = await repo.add_chat_to_tracking(
        admin_id=admin_id, chat_id=chat_id, is_source=True, is_target=True
    )

    # Assert
    assert access.id is not None
    assert access.admin_id == admin_id
    assert access.chat_id == chat_id
    assert access.is_source is True
    assert access.is_target is True


@pytest.mark.asyncio
async def test_remove_chat_from_tracking(db_manager: Any) -> None:
    """Тестирует удаление чата из отслеживания."""
    # Arrange
    repo = ChatTrackingRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_rem", username="admin_rem")
        chat = ChatSession(chat_id="-100_rem", title="Remove Chat")
        session.add_all([admin, chat])
        await session.commit()

        access = AdminChatAccess(admin_id=admin.id, chat_id=chat.id)
        session.add(access)
        await session.commit()
        admin_id, chat_id = admin.id, chat.id

    # Act
    result = await repo.remove_chat_from_tracking(admin_id=admin_id, chat_id=chat_id)
    # Повторное удаление
    result_non_existent = await repo.remove_chat_from_tracking(
        admin_id=admin_id, chat_id=chat_id
    )

    # Assert
    assert result is True
    assert result_non_existent is False

    # Проверяем отсутствие в БД
    access_in_db = await repo.get_access(admin_id=admin_id, chat_id=chat_id)
    assert access_in_db is None


@pytest.mark.asyncio
async def test_get_access(db_manager: Any) -> None:
    """Тестирует получение объекта доступа."""
    # Arrange
    repo = ChatTrackingRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_get", username="admin_get")
        chat = ChatSession(chat_id="-100_get", title="Get Chat")
        session.add_all([admin, chat])
        await session.commit()

        access = AdminChatAccess(admin_id=admin.id, chat_id=chat.id, is_source=True)
        session.add(access)
        await session.commit()
        admin_id, chat_id = admin.id, chat.id

    # Act
    found_access = await repo.get_access(admin_id=admin_id, chat_id=chat_id)
    not_found = await repo.get_access(admin_id=admin_id, chat_id=99999)

    # Assert
    assert found_access is not None
    assert found_access.admin_id == admin_id
    assert found_access.is_source is True
    assert not_found is None


@pytest.mark.asyncio
async def test_get_all_tracked_chats(db_manager: Any) -> None:
    """Тестирует получение всех отслеживаемых чатов администратора."""
    # Arrange
    from models import ChatSettings

    repo = ChatTrackingRepository(db_manager)
    async with db_manager.session() as session:
        admin = User(tg_id="admin_list", username="admin_list")
        c1 = ChatSession(chat_id="-101", title="Chat A")
        c2 = ChatSession(chat_id="-102", title="Chat B")
        c3 = ChatSession(chat_id="-103", title="Chat C")  # Не отслеживается
        session.add_all([admin, c1, c2, c3])
        await session.flush()  # Получаем ID чатов

        # Для прохождения теста на settings (так как в репозитории selectinload)
        # нужно, чтобы settings реально существовали в БД
        s1 = ChatSettings(chat_id=c1.id)
        s2 = ChatSettings(chat_id=c2.id)
        session.add_all([s1, s2])

        a1 = AdminChatAccess(admin_id=admin.id, chat_id=c1.id)
        a2 = AdminChatAccess(admin_id=admin.id, chat_id=c2.id)
        session.add_all([a1, a2])
        await session.commit()
        admin_id = admin.id

    # Act
    tracked_chats = await repo.get_all_tracked_chats(admin_id=admin_id)

    # Assert
    assert len(tracked_chats) == 2
    titles = [c.title for c in tracked_chats]
    assert "Chat A" in titles
    assert "Chat B" in titles
    assert "Chat C" not in titles

    # Проверяем, что объекты отсоединены от сессии (expunge_all)
    # но при этом данные настроек и доступов доступны (selectinload/joinedload)
    for chat in tracked_chats:
        assert chat.title is not None
        assert chat.settings is not None
        assert len(chat.admin_access) > 0
