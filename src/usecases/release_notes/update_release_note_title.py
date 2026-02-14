"""Use case: обновление заголовка релизной заметки."""

from dto.release_note import UpdateReleaseNoteTitleDTO
from exceptions import ReleaseNoteNotFoundError
from services.release_note_service import ReleaseNoteService


class UpdateReleaseNoteTitleUseCase:
    """Обновляет заголовок релизной заметки."""

    def __init__(self, release_note_service: ReleaseNoteService) -> None:
        self._service = release_note_service

    async def execute(self, dto: UpdateReleaseNoteTitleDTO) -> None:
        """Обновляет заголовок; при отсутствии заметки поднимает ReleaseNoteNotFoundError."""
        note = await self._service.get_note_by_id(dto.note_id)
        if not note:
            raise ReleaseNoteNotFoundError()

        success = await self._service.update_note_title(
            note_id=dto.note_id, new_title=dto.new_title
        )
        if not success:
            raise ReleaseNoteNotFoundError()
