from datetime import time
from typing import Any, Optional

import pytest

from models import ChatSession
from repositories.chat_repository import ChatRepository


@pytest.mark.asyncio
async def test_create_chat(db_manager: Any) -> None:
    """
    Тестирует создание нового чата.

    Проверяет:
    1. Присвоение ID.
    2. Корректность chat_id и title.
    3. Автоматическое создание настроек для чата.
    """
    # Arrange
    repo = ChatRepository(db_manager)
    chat_id = "-100111222_unique"
    title = "Test Repository Chat"

    # Act
    chat = await repo.create_chat(chat_id=chat_id, title=title)

    # Assert
    assert chat.id is not None
    assert chat.chat_id == chat_id
    assert chat.title == title

    # Проверяем, что настройки создались
    found_chat = await repo.get_chat_by_id(chat.id)
    assert found_chat.settings is not None


@pytest.mark.asyncio
async def test_get_chat_by_tgid(db_manager: Any) -> Optional[ChatSession]:
    """
    Тестирует получение чата по его Telegram ID.
    """
    # Arrange
    repo = ChatRepository(db_manager)
    chat_id = "-100333444_unique"
    async with db_manager.session() as session:
        chat = ChatSession(chat_id=chat_id, title="Stored Chat")
        session.add(chat)
        await session.commit()

    # Act
    found_chat = await repo.get_chat_by_tgid(chat_id)

    # Assert
    assert found_chat is not None
    assert found_chat.chat_id == chat_id
    assert found_chat.title == "Stored Chat"


@pytest.mark.asyncio
async def test_get_all(db_manager: Any) -> None:
    """
    Тестирует получение списка всех чатов.
    """
    # Arrange
    repo = ChatRepository(db_manager)
    await repo.create_chat(chat_id="-1", title="Chat 1")
    await repo.create_chat(chat_id="-2", title="Chat 2")

    # Act
    chats = await repo.get_all()

    # Assert
    assert len(chats) >= 2
    chat_ids = [c.chat_id for c in chats]
    assert "-1" in chat_ids
    assert "-2" in chat_ids


@pytest.mark.asyncio
async def test_update_chat_title(db_manager: Any) -> None:
    """
    Тестирует обновление заголовка чата.
    """
    # Arrange
    repo = ChatRepository(db_manager)
    chat = await repo.create_chat(chat_id="-100_upd", title="Old Title")

    # Act
    updated = await repo.update_chat(chat.id, "New Title")

    # Assert
    assert updated.title == "New Title"
    refreshed = await repo.get_chat_by_id(chat.id)
    assert refreshed.title == "New Title"


@pytest.mark.asyncio
async def test_toggle_antibot(db_manager: Any) -> None:
    """
    Тестирует переключение состояния антибота.
    """
    # Arrange
    repo = ChatRepository(db_manager)
    chat = await repo.create_chat(chat_id="-100_bot", title="Antibot Chat")
    chat_id_db: int = chat.id

    # Act (включаем)
    updated_chat = await repo.toggle_antibot(chat_id_db)

    # Assert
    assert updated_chat.settings.is_antibot_enabled is True

    # Act (выключаем)
    updated_chat2 = await repo.toggle_antibot(chat_id_db)
    assert updated_chat2.settings.is_antibot_enabled is False


@pytest.mark.asyncio
async def test_bind_archive_chat(db_manager: Any) -> None:
    """
    Тестирует привязку архивного чата к рабочему.
    """
    # Arrange
    repo = ChatRepository(db_manager)
    work_chat = await repo.create_chat(chat_id="-100_work", title="Work Chat")
    archive_tgid = "-100_archive"

    # Act (привязываем)
    # Метод сам создаст архивный чат, если его нет
    updated = await repo.bind_archive_chat(
        work_chat_id=work_chat.id,
        archive_chat_tgid=archive_tgid,
        archive_chat_title="Archive",
    )

    # Assert
    assert updated.archive_chat_id == archive_tgid

    # Перезапрашиваем чат, чтобы убедиться, что связь подгружается
    refreshed = await repo.get_chat_by_id(work_chat.id)
    assert refreshed.archive_chat_id == archive_tgid
    assert refreshed.archive_chat is not None
    assert refreshed.archive_chat.chat_id == archive_tgid


@pytest.mark.asyncio
async def test_update_work_hours(db_manager: Any) -> None:
    """
    Тестирует обновление рабочих часов чата.
    """
    # Arrange
    repo = ChatRepository(db_manager)
    chat = await repo.create_chat(chat_id="-100_hours", title="Hours Chat")
    start = time(9, 0)
    end = time(18, 0)
    tolerance = 15

    # Act
    updated = await repo.update_work_hours(
        chat_id=chat.id, start_time=start, end_time=end, tolerance=tolerance
    )

    # Assert
    assert updated.settings.start_time == start
    assert updated.settings.end_time == end
    assert updated.settings.tolerance == tolerance


@pytest.mark.asyncio
async def test_update_welcome_text(db_manager: Any) -> None:
    """
    Тестирует обновление приветственного текста.
    """
    # Arrange
    repo = ChatRepository(db_manager)
    chat = await repo.create_chat(chat_id="-100_welcome", title="Welcome Chat")
    text = "Hello! Please verify yourself."

    # Act
    updated = await repo.update_welcome_text(chat.id, text)

    # Assert
    assert updated.settings.welcome_text == text


@pytest.mark.asyncio
async def test_get_tracked_chats_for_admin(db_manager: Any) -> None:
    """
    Тестирует получение списка чатов для админа.
    """
    # Arrange
    repo = ChatRepository(db_manager)
    await repo.create_chat(chat_id="-track-1", title="Tracked 1")

    # Act
    chats = await repo.get_tracked_chats_for_admin(123)

    # Assert
    assert len(chats) >= 1
    assert any(c.chat_id == "-track-1" for c in chats)
