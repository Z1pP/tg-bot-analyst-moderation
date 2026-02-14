"""Use case: удаление релизной заметки."""

from dto.release_note import DeleteReleaseNoteDTO
from exceptions import ReleaseNoteNotFoundError
from services.release_note_service import ReleaseNoteService


class DeleteReleaseNoteUseCase:
    """Удаляет релизную заметку."""

    def __init__(self, release_note_service: ReleaseNoteService) -> None:
        self._service = release_note_service

    async def execute(self, dto: DeleteReleaseNoteDTO) -> None:
        """Удаляет заметку; при отсутствии поднимает ReleaseNoteNotFoundError."""
        note = await self._service.get_note_by_id(dto.note_id)
        if not note:
            raise ReleaseNoteNotFoundError()

        success = await self._service.delete_note(dto.note_id)
        if not success:
            raise ReleaseNoteNotFoundError()
