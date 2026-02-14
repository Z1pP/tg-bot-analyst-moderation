"""Use case: получение страницы списка релизных заметок."""

from constants.pagination import RELEASE_NOTES_PAGE_SIZE
from dto.release_note import (
    GetReleaseNotesPageDTO,
    ReleaseNoteItemDTO,
    ReleaseNotesPageResultDTO,
)
from services.release_note_service import ReleaseNoteService


class GetReleaseNotesPageUseCase:
    """Возвращает страницу заметок в виде DTO для меню."""

    def __init__(self, release_note_service: ReleaseNoteService) -> None:
        self._service = release_note_service

    async def execute(self, dto: GetReleaseNotesPageDTO) -> ReleaseNotesPageResultDTO:
        """Загружает страницу заметок и возвращает DTO с элементами списка."""
        page_size = dto.page_size if dto.page_size > 0 else RELEASE_NOTES_PAGE_SIZE
        offset = (dto.page - 1) * page_size

        notes = await self._service.get_notes(
            language=dto.language, limit=page_size, offset=offset
        )
        total_count = await self._service.count_notes(dto.language)
        total_pages = (total_count + page_size - 1) // page_size if page_size > 0 else 0

        items = [ReleaseNoteItemDTO(id=note.id, title=note.title) for note in notes]

        return ReleaseNotesPageResultDTO(
            notes=items,
            total_pages=total_pages,
            page=dto.page,
        )
