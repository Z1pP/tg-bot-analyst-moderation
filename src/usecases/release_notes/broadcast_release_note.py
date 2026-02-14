"""Use case: рассылка релизной заметки администраторам."""

from constants import Dialog
from constants.i18n import DEFAULT_LANGUAGE
from dto.release_note import (
    BroadcastRecipientDTO,
    BroadcastReleaseNoteDTO,
    BroadcastResultDTO,
    ReleaseNoteDetailResultDTO,
)
from exceptions import ReleaseNoteNotFoundError
from repositories import UserRepository
from services.release_note_service import ReleaseNoteService
from services.time_service import TimeZoneService


class BroadcastReleaseNoteUseCase:
    """Готовит список получателей и текст рассылки; хендлер выполняет отправку."""

    def __init__(
        self,
        release_note_service: ReleaseNoteService,
        user_repository: UserRepository,
    ) -> None:
        self._release_note_service = release_note_service
        self._user_repository = user_repository

    async def execute(self, dto: BroadcastReleaseNoteDTO) -> BroadcastResultDTO:
        """Возвращает список (chat_id, text) для отправки и DTO для экрана просмотра."""
        note = await self._release_note_service.get_note_by_id(dto.note_id)
        if not note:
            raise ReleaseNoteNotFoundError()

        note_language = (
            note.language.split("-")[0].lower() if note.language else DEFAULT_LANGUAGE
        )

        author_display_name = "Unknown"
        if note.author:
            author_display_name = note.author.username or str(note.author.tg_id)

        local_time = TimeZoneService.convert_to_local_time(note.created_at)
        date_str = local_time.strftime("%d.%m.%Y %H:%M") if local_time else ""

        broadcast_text = Dialog.ReleaseNotes.NOTE_DETAILS.format(
            title=note.title,
            content=note.content,
            author=author_display_name,
            date=date_str,
        )

        detail_dto = ReleaseNoteDetailResultDTO(
            note_id=note.id,
            title=note.title,
            content=note.content,
            author_display_name=author_display_name,
            date_str=date_str,
        )

        admins = await self._user_repository.get_all_admins()
        recipients: list[BroadcastRecipientDTO] = []

        for admin in admins:
            if not admin.tg_id or str(admin.tg_id) == dto.sender_tg_id:
                continue
            if note.author and str(admin.tg_id) == str(note.author.tg_id):
                continue
            admin_language = (
                admin.language.split("-")[0].lower()
                if admin.language
                else DEFAULT_LANGUAGE
            )
            if admin_language != note_language:
                continue
            try:
                chat_id = int(admin.tg_id)
            except (ValueError, TypeError):
                continue
            recipients.append(
                BroadcastRecipientDTO(chat_id=chat_id, text=broadcast_text)
            )

        return BroadcastResultDTO(recipients=recipients, detail_dto=detail_dto)
