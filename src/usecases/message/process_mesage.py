from dto.message import MessageDTO
from usecases.moderator_activity.simple import TrackSimpleModeratorActivityUseCase

from .save_message import SaveMessageUseCase


class ProcessMessageUseCase:
    def __init__(
        self,
        save_message_use_case: SaveMessageUseCase,
        track_activity_use_case: TrackSimpleModeratorActivityUseCase,
    ):
        self.save_message = save_message_use_case
        self.track_activity = track_activity_use_case

    async def execute(self, message_dto: MessageDTO):
        save_result = await self.save_message.execute(message_dto=message_dto)

        await self.track_activity.execute(
            user=save_result.user,
            message=save_result,
        )
