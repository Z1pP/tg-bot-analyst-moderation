from typing import Any

import pytest
from sqlalchemy import delete, select

from models import ReleaseNote, User
from repositories.release_note_repository import ReleaseNoteRepository


@pytest.fixture(autouse=True)
async def cleanup(db_manager: Any):
    """Очистка таблиц перед каждым тестом."""
    async with db_manager.session() as session:
        await session.execute(delete(ReleaseNote))
        await session.execute(delete(User))
        await session.commit()


async def create_test_user(session, tg_id: str, username: str) -> User:
    user = User(tg_id=tg_id, username=username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_create_release_note(db_manager: Any) -> None:
    """Тестирует создание релизной заметки."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "123", "author")

        repo = ReleaseNoteRepository(db_manager)
        title = "New Update"
        content = "Detailed changelog"
        language = "en"

        # Act
        note = await repo.create(title, content, language, user.id)

        # Assert
        assert note.id is not None
        assert note.title == title
        assert note.content == content
        assert note.language == language
        assert note.author_id == user.id


@pytest.mark.asyncio
async def test_get_release_note_by_id(db_manager: Any) -> None:
    """Тестирует получение заметки по ID."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "123", "author")
        repo = ReleaseNoteRepository(db_manager)
        note = await repo.create("Title", "Content", "ru", user.id)

        # Act
        found_note = await repo.get_by_id(note.id)

        # Assert
        assert found_note is not None
        assert found_note.id == note.id
        assert found_note.author.id == user.id


@pytest.mark.asyncio
async def test_get_by_id_not_found(db_manager: Any) -> None:
    """Тестирует получение несуществующей заметки."""
    repo = ReleaseNoteRepository(db_manager)

    # Act
    found_note = await repo.get_by_id(999)

    # Assert
    assert found_note is None


@pytest.mark.asyncio
async def test_get_all_release_notes(db_manager: Any) -> None:
    """Тестирует получение списка заметок с фильтрацией и пагинацией."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "1", "author")
        repo = ReleaseNoteRepository(db_manager)

        # Create 3 notes in RU, 1 in EN
        await repo.create("RU 1", "C1", "ru", user.id)
        await repo.create("RU 2", "C2", "ru", user.id)
        await repo.create("RU 3", "C3", "ru", user.id)
        await repo.create("EN 1", "C4", "en", user.id)

        # Act
        ru_notes = await repo.get_all(language="ru", limit=2, offset=0)

        # Assert
        assert len(ru_notes) == 2
        assert all(n.language == "ru" for n in ru_notes)
        # Check ordering (latest first)
        assert ru_notes[0].title == "RU 3"
        assert ru_notes[1].title == "RU 2"


@pytest.mark.asyncio
async def test_count_release_notes(db_manager: Any) -> None:
    """Тестирует подсчет количества заметок."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "1", "author")
        repo = ReleaseNoteRepository(db_manager)

        await repo.create("RU 1", "C1", "ru", user.id)
        await repo.create("RU 2", "C2", "ru", user.id)
        await repo.create("EN 1", "C1", "en", user.id)

        # Act & Assert
        assert await repo.count(language="ru") == 2
        assert await repo.count(language="en") == 1
        assert await repo.count(language="fr") == 0


@pytest.mark.asyncio
async def test_update_release_note(db_manager: Any) -> None:
    """Тестирует обновление заголовка и содержимого."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "1", "author")
        repo = ReleaseNoteRepository(db_manager)
        note = await repo.create("Old Title", "Old Content", "ru", user.id)

        # Act
        title_updated = await repo.update_title(note.id, "New Title")
        content_updated = await repo.update_content(note.id, "New Content")

        # Assert
        assert title_updated is True
        assert content_updated is True

        async with db_manager.session() as s:
            res = await s.execute(select(ReleaseNote).where(ReleaseNote.id == note.id))
            updated_note = res.scalar_one()
            assert updated_note.title == "New Title"
            assert updated_note.content == "New Content"


@pytest.mark.asyncio
async def test_update_not_found(db_manager: Any) -> None:
    """Тестирует обновление несуществующей заметки."""
    repo = ReleaseNoteRepository(db_manager)

    assert await repo.update_title(999, "Title") is False
    assert await repo.update_content(999, "Content") is False


@pytest.mark.asyncio
async def test_delete_release_note(db_manager: Any) -> None:
    """Тестирует удаление заметки."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "1", "author")
        repo = ReleaseNoteRepository(db_manager)
        note = await repo.create("Title", "Content", "ru", user.id)

        # Act
        deleted = await repo.delete(note.id)

        # Assert
        assert deleted is True
        assert await repo.get_by_id(note.id) is None

        # Test delete non-existent
        assert await repo.delete(999) is False
