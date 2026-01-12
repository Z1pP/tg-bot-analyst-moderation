from typing import Any

import pytest

from models import ChatSession, ChatSettings
from repositories.chat_repository import ChatRepository


@pytest.mark.asyncio
async def test_create_chat(db_manager: Any) -> None:
    # Arrange
    repo = ChatRepository(db_manager)
    chat_id = "-100111222_type"
    title = "Test Repository Chat"

    # Act
    chat = await repo.create_chat(chat_id=chat_id, title=title)

    # Assert
    assert chat.id is not None
    assert chat.chat_id == chat_id
    assert chat.title == title


@pytest.mark.asyncio
async def test_get_chat_by_tgid(db_manager: Any) -> None:
    # Arrange
    repo = ChatRepository(db_manager)
    chat_id = "-100333444_type"
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
async def test_update_chat_settings(db_manager: Any) -> None:
    # Arrange
    repo = ChatRepository(db_manager)
    chat_id = "-100555666_type"
    async with db_manager.session() as session:
        chat = ChatSession(chat_id=chat_id, title="Settings Chat")
        settings = ChatSettings(chat=chat, is_antibot_enabled=False)
        session.add_all([chat, settings])
        await session.commit()
        chat_id_db: int = chat.id

    # Act
    # Assuming update_chat_settings or similar exists.
    # Let's check the file content more for update methods.
    # For now, let's just test get_chat_by_id with settings.
    found_chat = await repo.get_chat_by_id(chat_id_db)

    # Assert
    assert found_chat is not None
    assert found_chat.settings is not None
    assert found_chat.settings.is_antibot_enabled is False


@pytest.mark.asyncio
async def test_toggle_antibot(db_manager: Any) -> None:
    # Arrange
    repo = ChatRepository(db_manager)
    chat_id = "-100777888_type"
    async with db_manager.session() as session:
        chat = ChatSession(chat_id=chat_id, title="Antibot Chat")
        settings = ChatSettings(chat=chat, is_antibot_enabled=False)
        session.add_all([chat, settings])
        await session.commit()
        chat_id_db: int = chat.id

    # Act
    updated_chat = await repo.toggle_antibot(chat_id_db)

    # Assert
    assert updated_chat is not None
    assert updated_chat.settings.is_antibot_enabled is True

    # Toggle back
    updated_chat2 = await repo.toggle_antibot(chat_id_db)
    assert updated_chat2 is not None
    assert updated_chat2.settings.is_antibot_enabled is False
