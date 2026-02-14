"""Use case: получение одной релизной заметки для отображения."""

from dto.release_note import (
    GetReleaseNoteByIdDTO,
    ReleaseNoteDetailResultDTO,
)
from exceptions import ReleaseNoteNotFoundError
from services.release_note_service import ReleaseNoteService
from services.time_service import TimeZoneService


class GetReleaseNoteUseCase:
    """Возвращает DTO заметки для экрана просмотра (без мутации модели)."""

    def __init__(self, release_note_service: ReleaseNoteService) -> None:
        self._service = release_note_service

    async def execute(self, dto: GetReleaseNoteByIdDTO) -> ReleaseNoteDetailResultDTO:
        """Загружает заметку и возвращает DTO с полями для отображения."""
        note = await self._service.get_note_by_id(dto.note_id)
        if not note:
            raise ReleaseNoteNotFoundError()

        author_display_name = "Unknown"
        if note.author:
            author_display_name = note.author.username or str(note.author.tg_id)

        local_time = TimeZoneService.convert_to_local_time(note.created_at)
        date_str = local_time.strftime("%d.%m.%Y %H:%M") if local_time else ""

        return ReleaseNoteDetailResultDTO(
            note_id=note.id,
            title=note.title,
            content=note.content,
            author_display_name=author_display_name,
            date_str=date_str,
        )
