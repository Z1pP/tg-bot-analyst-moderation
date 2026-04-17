"""Тесты буфера автомодерации (Redis Lua) с моком клиента."""

from unittest.mock import MagicMock

import pytest

from dto.automoderation import AutoModerationBufferItemDTO
from services.automoderation_buffer_service import AutoModerationBufferService


def _item(
    *,
    user_tg_id: int = 1,
    message_id: int = 10,
    text: str = "hello",
    username: str | None = "u",
) -> AutoModerationBufferItemDTO:
    return AutoModerationBufferItemDTO(
        username=username,
        user_tg_id=user_tg_id,
        message_id=message_id,
        message_text=text,
    )


@pytest.mark.asyncio
async def test_append_returns_none_until_flush() -> None:
    async def lua(keys: list[str], args: list[str]) -> None:
        return None

    redis = MagicMock()
    script_fn = MagicMock(side_effect=lua)
    redis.register_script.return_value = script_fn

    svc = AutoModerationBufferService(redis)
    r1 = await svc.append_text_message("-100", _item(), batch_size=5)

    assert r1 is None
    script_fn.assert_called_once()
    call = script_fn.call_args
    assert call.kwargs["keys"] == ["automod:buffer:-100"]
    assert call.kwargs["args"][1] == "5"


@pytest.mark.asyncio
async def test_append_returns_batch_after_flush() -> None:
    raw0 = _item(user_tg_id=2, message_id=20, text="a").model_dump_json()
    raw1 = _item(user_tg_id=3, message_id=30, text="b").model_dump_json()
    payload = [raw0.encode("utf-8"), raw1]

    async def lua(keys: list[str], args: list[str]) -> list:
        return payload

    redis = MagicMock()
    script_fn = MagicMock(side_effect=lua)
    redis.register_script.return_value = script_fn

    svc = AutoModerationBufferService(redis)
    batch = await svc.append_text_message("-100", _item(), batch_size=2)

    assert batch is not None
    assert len(batch) == 2
    assert batch[0].user_tg_id == 2
    assert batch[1].message_text == "b"


@pytest.mark.asyncio
async def test_append_on_redis_error_returns_none() -> None:
    from redis.exceptions import ConnectionError as RedisConnectionError

    async def lua_fail(*args, **kwargs):
        raise RedisConnectionError("down")

    redis = MagicMock()
    redis.register_script.return_value = MagicMock(side_effect=lua_fail)

    svc = AutoModerationBufferService(redis)
    r = await svc.append_text_message("-100", _item(), batch_size=3)
    assert r is None
