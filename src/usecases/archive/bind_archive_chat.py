"""Use case: привязка архивного чата к рабочему по hash."""

from typing import Optional

from dto.chat_dto import BindArchiveChatDTO
from models import ChatSession
from services.chat import ArchiveBindService, ChatService


class BindArchiveChatUseCase:
    """
    Извлекает данные из hash привязки и привязывает архивный чат к рабочему.
    Возвращает рабочий чат при успехе или None.
    """

    def __init__(
        self,
        archive_bind_service: ArchiveBindService,
        chat_service: ChatService,
    ):
        self._archive_bind_service = archive_bind_service
        self._chat_service = chat_service

    async def execute(self, dto: BindArchiveChatDTO) -> Optional[tuple[int, Optional[int], Optional[ChatSession]]]:
        """
        Выполняет привязку.

        Returns:
            (work_chat_id, admin_tg_id, work_chat) при валидном hash и успешной привязке.
            (work_chat_id, admin_tg_id, None) если hash валиден, но привязка не удалась.
            None если hash невалиден.
        """
        bind_data = self._archive_bind_service.extract_bind_data(dto.bind_hash)
        if not bind_data:
            return None

        work_chat_id, admin_tg_id = bind_data
        work_chat = await self._chat_service.bind_archive_chat(
            work_chat_id=work_chat_id,
            archive_chat_tgid=dto.archive_chat_tgid,
            archive_chat_title=dto.archive_chat_title,
        )
        return (work_chat_id, admin_tg_id, work_chat)