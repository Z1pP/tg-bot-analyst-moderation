from typing import Any, Optional, Type, TypeVar, Union
from urllib.parse import urljoin

from aiohttp import ClientSession
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseApiClient:
    def __init__(self, base_url: str, session: ClientSession) -> None:
        self._base_url = base_url
        self._session = session

    async def _get_session(self) -> ClientSession:
        if self._session is None or self._session.closed:
            self._session = ClientSession()
        return self._session

    async def make_request(
        self,
        method: str,
        endpoint: str,
        response_model: Optional[Type[T]] = None,
        **kwargs: Any,
    ) -> Union[T, dict[str, Any]]:
        """Общий метод для выполнения запросов с обработкой ошибок."""
        session = await self._get_session()
        url = urljoin(self._base_url, endpoint)

        async with session.request(method, url, **kwargs) as response:
            response.raise_for_status()
            data = await response.json()

            if response_model:
                return response_model.model_validate(data)
            return data

    async def close(self) -> None:
        """Явное закрытие сессии."""
        if self._session and not self._session.closed:
            await self._session.close()

    async def __aenter__(self) -> "BaseApiClient":
        return self

    async def __aexit__(self, _: Any, __: Any, ___: Any) -> None:
        await self.close()
