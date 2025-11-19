from typing import Sequence

from models.release_note import ReleaseNote
from repositories.release_note_repository import ReleaseNoteRepository


class ReleaseNoteService:
    def __init__(self, repository: ReleaseNoteRepository):
        self.repository = repository

    async def create_note(
        self, title: str, content: str, language: str, author_id: int
    ) -> ReleaseNote:
        """
        Создает новую релизную заметку.
        """
        return await self.repository.create(title, content, language, author_id)

    async def get_notes(
        self, language: str, limit: int = 10, offset: int = 0
    ) -> Sequence[ReleaseNote]:
        """
        Получает список релизных заметок.
        """
        return await self.repository.get_all(language, limit, offset)

    async def get_note_by_id(self, note_id: int) -> ReleaseNote | None:
        """
        Получает релизную заметку по ID.
        """
        return await self.repository.get_by_id(note_id)

    async def count_notes(self, language: str) -> int:
        """
        Возвращает количество релизных заметок.
        """
        return await self.repository.count(language)

    async def delete_note(self, note_id: int) -> bool:
        """
        Удаляет релизную заметку.
        """
        return await self.repository.delete(note_id)

    async def update_note_title(self, note_id: int, new_title: str) -> bool:
        """
        Обновляет заголовок релизной заметки.
        """
        return await self.repository.update_title(note_id, new_title)

    async def update_note_content(self, note_id: int, new_content: str) -> bool:
        """
        Обновляет содержимое релизной заметки.
        """
        return await self.repository.update_content(note_id, new_content)
