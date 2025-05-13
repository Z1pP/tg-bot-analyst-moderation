from typing import Optional

from models import ChatMessage, ModeratorActivity, User
from repositories import ActivityRepository

from .base import BaseModeratorActivityTrackerUseCase


class TrackSimpleModeratorActivityUseCase(BaseModeratorActivityTrackerUseCase):
    def __init__(self, activivty_repository: ActivityRepository):
        self.activity_repository = activivty_repository
        super().__init__()

    async def execute(
        self,
        user: User,
        message: ChatMessage,
    ) -> Optional[ModeratorActivity]:
        """
        Трекает все сообщения которые не являются reply на другие сообщения
        """
        last_activity = await self.activity_repository.get_last_activity(
            user_id=user.id, chat_id=message.chat_id
        )

        if not last_activity:
            # создаем новую активность
            return await self.activity_repository.create_simple_activity(
                user_id=user.id,
                chat_id=message.chat_id,
                message_id=message.id,
            )
