from typing import Optional

from dto.message import CreateMessageDTO, ResultMessageDTO
from usecases.moderator_activity import (
    TrackModeratorActivityUseCase,
)

from .save_message import SaveMessageUseCase


class ProcessMessageUseCase:
    def __init__(
        self,
        save_message_use_case: SaveMessageUseCase,
        track_activity_use_case: TrackModeratorActivityUseCase,
    ):
        self.save_message = save_message_use_case
        self.track_activity = track_activity_use_case

    async def execute(
        self,
        message_dto: CreateMessageDTO,
    ) -> Optional[ResultMessageDTO]:
        # Сохраняем сообщение
        result_msg = await self.save_message.execute(message_dto=message_dto)

        # Трекаем в активность
        await self.track_activity.execute(message_dto=result_msg)

        return result_msg
