import logging

from dto.membership_event import RecordChatMembershipEventDTO
from repositories import ChatMembershipEventRepository
from services import ChatService

logger = logging.getLogger(__name__)


class RecordChatMembershipEventUseCase:
    """Запись события вступления или ухода участника (если чат есть в БД)."""

    def __init__(
        self,
        chat_service: ChatService,
        membership_event_repository: ChatMembershipEventRepository,
    ) -> None:
        self._chat_service = chat_service
        self._membership_event_repository = membership_event_repository

    async def execute(self, dto: RecordChatMembershipEventDTO) -> None:
        chat = await self._chat_service.get_chat(chat_tgid=dto.chat_tgid)
        if chat is None:
            logger.info(
                "Чат %s не в БД — событие состава (%s, user %s) не записано",
                dto.chat_tgid,
                dto.event_type.value,
                dto.user_tgid,
            )
            return

        await self._membership_event_repository.add(
            chat_id=chat.id,
            user_tgid=dto.user_tgid,
            event_type=dto.event_type,
        )
