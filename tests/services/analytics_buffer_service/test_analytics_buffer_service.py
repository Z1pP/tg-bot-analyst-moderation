"""Тесты для AnalyticsBufferService: add_message, pop_messages, trim_messages с моком Redis."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock

import pytest

from dto.buffer import BufferedMessageDTO
from services.analytics_buffer_service import AnalyticsBufferService


@pytest.fixture
def buffer_service() -> AnalyticsBufferService:
    """Сервис с подменённым подключением к Redis."""
    mock_redis = AsyncMock()
    svc = AnalyticsBufferService(redis_client=mock_redis)
    svc._connected = True
    return svc


@pytest.fixture
def sample_message_dto() -> BufferedMessageDTO:
    return BufferedMessageDTO(
        chat_id=1,
        user_id=2,
        message_id="3",
        message_type="text",
        content_type="text",
        text="hello",
        created_at=datetime.now(timezone.utc),
    )


@pytest.mark.asyncio
async def test_add_message_calls_rpush(
    buffer_service: AnalyticsBufferService,
    sample_message_dto: BufferedMessageDTO,
) -> None:
    """add_message добавляет сериализованное сообщение в буфер через rpush."""
    await buffer_service.add_message(sample_message_dto)
    buffer_service._redis.rpush.assert_called_once()
    call_args = buffer_service._redis.rpush.call_args[0]
    assert call_args[0] == AnalyticsBufferService.REDIS_KEY_MESSAGES
    assert b"chat_id" in call_args[1] or b"message_id" in call_args[1]


@pytest.mark.asyncio
async def test_pop_messages_returns_deserialized_list(
    buffer_service: AnalyticsBufferService,
    sample_message_dto: BufferedMessageDTO,
) -> None:
    """pop_messages читает пачку из Redis и возвращает список DTO."""
    json_bytes = sample_message_dto.model_dump_json().encode("utf-8")
    buffer_service._redis.lrange = AsyncMock(return_value=[json_bytes])
    result = await buffer_service.pop_messages(count=10)
    assert len(result) == 1
    assert result[0].chat_id == sample_message_dto.chat_id
    assert result[0].message_id == sample_message_dto.message_id
    buffer_service._redis.lrange.assert_called_once_with(
        AnalyticsBufferService.REDIS_KEY_MESSAGES, 0, 9
    )


@pytest.mark.asyncio
async def test_pop_messages_empty_returns_empty_list(
    buffer_service: AnalyticsBufferService,
) -> None:
    """pop_messages при пустом буфере возвращает пустой список."""
    buffer_service._redis.lrange = AsyncMock(return_value=[])
    result = await buffer_service.pop_messages(count=5)
    assert result == []


@pytest.mark.asyncio
async def test_trim_messages_calls_ltrim(
    buffer_service: AnalyticsBufferService,
) -> None:
    """trim_messages удаляет обработанные элементы через ltrim."""
    await buffer_service.trim_messages(count=3)
    buffer_service._redis.ltrim.assert_called_once_with(
        AnalyticsBufferService.REDIS_KEY_MESSAGES, 3, -1
    )


@pytest.mark.asyncio
async def test_add_message_when_connection_fails_does_not_raise(
    sample_message_dto: BufferedMessageDTO,
) -> None:
    """При недоступности Redis add_message не выбрасывает исключение."""
    mock_redis = AsyncMock()
    svc = AnalyticsBufferService(redis_client=mock_redis)
    svc._ensure_connection = AsyncMock(return_value=False)
    await svc.add_message(sample_message_dto)
    # Не должно быть исключения
    assert True


@pytest.mark.asyncio
async def test_pop_messages_when_connection_fails_returns_empty(
    buffer_service: AnalyticsBufferService,
) -> None:
    """При недоступности Redis pop_messages возвращает пустой список."""
    buffer_service._ensure_connection = AsyncMock(return_value=False)
    result = await buffer_service.pop_messages(count=5)
    assert result == []


@pytest.mark.asyncio
async def test_add_reaction_calls_rpush(
    buffer_service: AnalyticsBufferService,
) -> None:
    """add_reaction добавляет реакцию в буфер через rpush."""
    from dto.buffer import BufferedReactionDTO

    dto = BufferedReactionDTO(
        chat_id=1,
        user_id=2,
        message_id="3",
        action="add",
        emoji="👍",
        message_url="https://t.me/c/1/2",
        created_at=datetime.now(timezone.utc),
    )
    await buffer_service.add_reaction(dto)
    buffer_service._redis.rpush.assert_called_once()
    assert (
        buffer_service._redis.rpush.call_args[0][0]
        == AnalyticsBufferService.REDIS_KEY_REACTIONS
    )


@pytest.mark.asyncio
async def test_trim_reactions_calls_ltrim(
    buffer_service: AnalyticsBufferService,
) -> None:
    """trim_reactions удаляет обработанные реакции через ltrim."""
    await buffer_service.trim_reactions(count=2)
    buffer_service._redis.ltrim.assert_called_once_with(
        AnalyticsBufferService.REDIS_KEY_REACTIONS, 2, -1
    )


@pytest.mark.asyncio
async def test_re_add_replies_calls_rpush(
    buffer_service: AnalyticsBufferService,
) -> None:
    """re_add_replies возвращает reply в буфер через rpush."""
    from dto.buffer import BufferedMessageReplyDTO

    dtos = [
        BufferedMessageReplyDTO(
            chat_id=1,
            original_message_url="url1",
            reply_message_id_str="100",
            reply_user_id=2,
            response_time_seconds=10,
            created_at=datetime.now(timezone.utc),
        ),
    ]
    await buffer_service.re_add_replies(dtos)
    buffer_service._redis.rpush.assert_called_once()
    call_args = buffer_service._redis.rpush.call_args
    assert call_args[0][0] == AnalyticsBufferService.REDIS_KEY_REPLIES
    assert len(call_args[0]) == 2  # key + value(s)
    assert b"chat_id" in call_args[0][1] or b"original_message_url" in call_args[0][1]


@pytest.mark.asyncio
async def test_re_add_replies_empty_does_nothing(
    buffer_service: AnalyticsBufferService,
) -> None:
    """re_add_replies с пустым списком не вызывает Redis."""
    await buffer_service.re_add_replies([])
    buffer_service._redis.rpush.assert_not_called()
