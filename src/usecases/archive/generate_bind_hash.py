"""Use case: генерация hash для привязки архивного чата."""

from dto.chat_dto import GenerateArchiveBindHashDTO
from services.chat import ArchiveBindService


class GenerateArchiveBindHashUseCase:
    """Генерирует уникальный hash для привязки архивного чата к рабочему."""

    def __init__(self, archive_bind_service: ArchiveBindService) -> None:
        self._archive_bind_service = archive_bind_service

    async def execute(self, dto: GenerateArchiveBindHashDTO) -> str:
        result: str = self._archive_bind_service.generate_bind_hash(
            chat_id=dto.chat_id,
            admin_tg_id=dto.admin_tg_id,
        )
        return result
