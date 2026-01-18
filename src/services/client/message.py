from typing import Optional

from constants.endponts import CREATE_MESSAGE
from dto.message import CreateMessageDTO, ResultMessageDTO

from .base import BaseApiClient


class MessageClient(BaseApiClient):
    async def create_message(self, dto: CreateMessageDTO) -> Optional[ResultMessageDTO]:
        return await self.make_request(
            method="POST",
            endpoint=CREATE_MESSAGE,
            response_model=ResultMessageDTO,
            json=dto.model_dump(mode="json"),
        )
