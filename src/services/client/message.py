from typing import Optional, cast

from constants.endpoints import CREATE_MESSAGE
from dto.message import CreateMessageDTO, ResultMessageDTO

from .base import BaseApiClient


class MessageClient(BaseApiClient):
    async def create_message(self, dto: CreateMessageDTO) -> Optional[ResultMessageDTO]:
        return cast(
            Optional[ResultMessageDTO],
            await self.make_request(
                method="POST",
                endpoint=CREATE_MESSAGE,
                response_model=ResultMessageDTO,
                json=dto.model_dump(mode="json"),
            ),
        )
