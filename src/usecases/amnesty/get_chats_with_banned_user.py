from typing import List, Optional
from dto import ChatDTO, AmnestyUserDTO
from repositories import ChatTrackingRepository, UserChatStatusRepository
from services import UserService


class GetChatsWithBannedUserUseCase:
    def __init__(
        self,
        user_service: UserService,
        chat_tracking_repository: ChatTrackingRepository,
        user_chat_status_repository: UserChatStatusRepository,
    ):
        self.user_service = user_service
        self.chat_tracking_repository = chat_tracking_repository
        self.user_chat_status_repository = user_chat_status_repository

    async def execute(self, dto: AmnestyUserDTO) -> Optional[List[ChatDTO]]:
        admin = await self.user_service.get_user(tg_id=dto.admin_tgid)

        # Получаем все отслеживаемые чаты администратора
        tracked_chats = await self.chat_tracking_repository.get_all_tracked_chats(
            admin_id=admin.id
        )

        # Среди отслеживаемых чатов администратора ищем где пользователь заблокирован
        chat_dtos = []
        for chat in tracked_chats:
            status = await self.user_chat_status_repository.get_status(
                user_id=dto.violator_id,
                chat_id=chat.id,
            )

            if status and status.is_banned:
                chat_dtos.append(
                    ChatDTO(
                        id=chat.id,
                        tg_id=chat.chat_id,
                        title=chat.title,
                    )
                )

        if not chat_dtos:
            return None

        return chat_dtos
