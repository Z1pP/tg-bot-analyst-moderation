"""Use case: создание релизной заметки."""

from dto.release_note import CreateReleaseNoteDTO
from exceptions import UserNotFoundException
from services.release_note_service import ReleaseNoteService
from services.user import UserService


class CreateReleaseNoteUseCase:
    """Создаёт релизную заметку от имени пользователя по author_tg_id."""

    def __init__(
        self,
        release_note_service: ReleaseNoteService,
        user_service: UserService,
    ) -> None:
        self._release_note_service = release_note_service
        self._user_service = user_service

    async def execute(self, dto: CreateReleaseNoteDTO) -> None:
        """Получает пользователя по tg_id, создаёт заметку."""
        user = await self._user_service.get_user(tg_id=dto.author_tg_id)
        if not user:
            raise UserNotFoundException()

        await self._release_note_service.create_note(
            title=dto.title,
            content=dto.content,
            language=dto.language,
            author_id=user.id,
        )
