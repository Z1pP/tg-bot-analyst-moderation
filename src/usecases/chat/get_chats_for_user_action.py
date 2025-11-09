from typing import List, Optional

from dto import ChatDTO
from repositories import ChatTrackingRepository
from services import BotPermissionService, UserService


class GetChatsForUserActionUseCase:
    """Возвращает чаты где можно выполнить действие над пользователем."""

    def __init__(
        self,
        user_service: UserService,
        chat_tracking_repository: ChatTrackingRepository,
        bot_permission_service: BotPermissionService,
    ):
        self._user_service = user_service
        self._chat_tracking_repository = chat_tracking_repository
        self._bot_permission_service = bot_permission_service

    async def execute(
        self,
        admin_tgid: str,
        user_tgid: str,
    ) -> Optional[List[ChatDTO]]:
        """
        Возвращает чаты где:
        1) Чат в отслеживании администратора
        2) Пользователь является членом группы
        3) Пользователь не заблокирован
        """
        admin = await self._user_service.get_user(tg_id=admin_tgid)
        if not admin:
            return []

        tracked_chats = await self._chat_tracking_repository.get_all_tracked_chats(
            admin_id=admin.id
        )

        if not tracked_chats:
            return []

        result_chats = []
        for chat in tracked_chats:
            try:
                member = await self._bot_permission_service.bot.get_chat_member(
                    chat_id=chat.chat_id,
                    user_id=int(user_tgid),
                )

                # Проверяем что пользователь член группы и не забанен
                if member.status not in ["kicked", "left"]:
                    result_chats.append(
                        ChatDTO(
                            id=chat.id,
                            title=chat.title,
                            tg_id=chat.chat_id,
                        )
                    )
            except Exception:
                # Пользователь не найден в чате или ошибка API
                continue

        return result_chats
