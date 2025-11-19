from typing import Sequence

from sqlalchemy import func, select
from sqlalchemy.orm import selectinload

from database.session import DatabaseContextManager
from models.release_note import ReleaseNote


class ReleaseNoteRepository:
    def __init__(self, db_manager: DatabaseContextManager):
        self._db = db_manager

    async def create(
        self, title: str, content: str, language: str, author_id: int
    ) -> ReleaseNote:
        """
        Создает новую релизную заметку.
        """
        release_note = ReleaseNote(
            title=title,
            content=content,
            language=language,
            author_id=author_id,
        )
        async with self._db.session() as session:
            session.add(release_note)
            await session.commit()
            await session.refresh(release_note)
        return release_note

    async def get_all(
        self, language: str, limit: int = 10, offset: int = 0
    ) -> Sequence[ReleaseNote]:
        """
        Получает список релизных заметок с пагинацией и фильтрацией по языку.
        """
        stmt = (
            select(ReleaseNote)
            .where(ReleaseNote.language == language)
            .order_by(ReleaseNote.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        async with self._db.session() as session:
            result = await session.execute(stmt)
        return result.scalars().all()

    async def get_by_id(self, note_id: int) -> ReleaseNote | None:
        """
        Получает релизную заметку по ID.
        """
        stmt = (
            select(ReleaseNote)
            .options(selectinload(ReleaseNote.author))
            .where(ReleaseNote.id == note_id)
        )
        async with self._db.session() as session:
            result = await session.execute(stmt)
        return result.scalar_one_or_none()

    async def count(self, language: str) -> int:
        """
        Возвращает общее количество релизных заметок для указанного языка.
        """
        stmt = select(func.count(ReleaseNote.id)).where(
            ReleaseNote.language == language
        )
        async with self._db.session() as session:
            result = await session.execute(stmt)
        return result.scalar_one()

    async def delete(self, note_id: int) -> bool:
        """
        Удаляет релизную заметку по ID.
        """
        async with self._db.session() as session:
            stmt = select(ReleaseNote).where(ReleaseNote.id == note_id)
            result = await session.execute(stmt)
            note = result.scalar_one_or_none()
            if note:
                await session.delete(note)
                await session.commit()
                return True
            return False

    async def update_title(self, note_id: int, new_title: str) -> bool:
        """
        Обновляет заголовок релизной заметки.
        """
        async with self._db.session() as session:
            stmt = select(ReleaseNote).where(ReleaseNote.id == note_id)
            result = await session.execute(stmt)
            note = result.scalar_one_or_none()
            if note:
                note.title = new_title
                await session.commit()
                return True
            return False

    async def update_content(self, note_id: int, new_content: str) -> bool:
        """
        Обновляет содержимое релизной заметки.
        """
        async with self._db.session() as session:
            stmt = select(ReleaseNote).where(ReleaseNote.id == note_id)
            result = await session.execute(stmt)
            note = result.scalar_one_or_none()
            if note:
                note.content = new_content
                await session.commit()
                return True
            return False
