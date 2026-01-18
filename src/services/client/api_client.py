from aiohttp import ClientSession

from .message import MessageClient


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self._session = ClientSession()
        # Other clients
        self.message = MessageClient(base_url, self._session)

    async def close(self) -> None:
        if not self._session.closed:
            await self._session.close()
