"""Use case: обновление содержимого релизной заметки."""

from dto.release_note import UpdateReleaseNoteContentDTO
from exceptions import ReleaseNoteNotFoundError
from services.release_note_service import ReleaseNoteService


class UpdateReleaseNoteContentUseCase:
    """Обновляет содержимое релизной заметки."""

    def __init__(self, release_note_service: ReleaseNoteService) -> None:
        self._service = release_note_service

    async def execute(self, dto: UpdateReleaseNoteContentDTO) -> None:
        """Обновляет содержимое; при отсутствии заметки поднимает ReleaseNoteNotFoundError."""
        note = await self._service.get_note_by_id(dto.note_id)
        if not note:
            raise ReleaseNoteNotFoundError()

        success = await self._service.update_note_content(
            note_id=dto.note_id, new_content=dto.new_content
        )
        if not success:
            raise ReleaseNoteNotFoundError()
