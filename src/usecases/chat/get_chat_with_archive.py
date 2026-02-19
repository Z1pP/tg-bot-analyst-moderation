"""Use case: получение чата с архивным каналом по id или tgid."""

from typing import Optional

from dto.chat_dto import GetChatWithArchiveDTO
from exceptions import ValidationException
from models import ChatSession
from services.chat.chat_service import ChatService


class GetChatWithArchiveUseCase:
    """Возвращает чат и его архивный чат (если есть) по chat_id или chat_tgid."""

    def __init__(self, chat_service: ChatService):
        self._chat_service = chat_service

    async def execute(self, dto: GetChatWithArchiveDTO) -> Optional[ChatSession]:
        if dto.chat_id is None and dto.chat_tgid is None:
            raise ValidationException(
                message="Необходимо передать chat_id или chat_tgid"
            )
        return await self._chat_service.get_chat_with_archive(
            chat_id=dto.chat_id,
            chat_tgid=dto.chat_tgid,
        )
