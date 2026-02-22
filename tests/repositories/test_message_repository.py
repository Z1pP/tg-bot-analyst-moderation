"""Тесты для MessageRepository."""

from datetime import datetime, timedelta, timezone
from typing import Any

import pytest

from dto.buffer import BufferedMessageDTO
from models import ChatMessage, ChatSession, User
from repositories.message_repository import MessageRepository


@pytest.mark.asyncio
async def test_get_messages_for_summary_empty(db_manager: Any) -> None:
    """Пустой список сообщений для саммари при отсутствии данных."""
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_msg_sum", title="Msg Sum")
        session.add(chat)
        await session.commit()
        chat_id = chat.id

    repo = MessageRepository(db_manager)
    result = await repo.get_messages_for_summary(chat_id=chat_id, limit=10)
    assert result == []


@pytest.mark.asyncio
async def test_get_messages_for_summary_with_messages(db_manager: Any) -> None:
    """Получение текстовых сообщений для саммари."""
    now = datetime.now(timezone.utc)
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_msg_cont", title="Msg Cont")
        user = User(tg_id="msg_u", username="msg_user")
        session.add_all([chat, user])
        await session.flush()
        m = ChatMessage(
            chat_id=chat.id,
            user_id=user.id,
            message_id="m1",
            message_type="text",
            content_type="text",
            text="Hello",
            created_at=now,
        )
        session.add(m)
        await session.commit()
        chat_id = chat.id

    repo = MessageRepository(db_manager)
    result = await repo.get_messages_for_summary(chat_id=chat_id, limit=10)
    assert len(result) == 1
    assert result[0] == ("Hello", "msg_user")


@pytest.mark.asyncio
async def test_get_messages_by_period_date_for_users_empty(db_manager: Any) -> None:
    """Пустой список при пустом user_ids."""
    repo = MessageRepository(db_manager)
    now = datetime.now(timezone.utc)
    result = await repo.get_messages_by_period_date_for_users(
        user_ids=[], start_date=now - timedelta(days=1), end_date=now
    )
    assert result == []


@pytest.mark.asyncio
async def test_get_messages_by_chat_id_and_period(db_manager: Any) -> None:
    """Сообщения чата за период."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(hours=1)
    end = now + timedelta(hours=1)
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_msg_per", title="Msg Per")
        user = User(tg_id="msg_p", username="msg_p")
        session.add_all([chat, user])
        await session.flush()
        m = ChatMessage(
            chat_id=chat.id,
            user_id=user.id,
            message_id="mp1",
            message_type="text",
            content_type="text",
            text="Hi",
            created_at=now,
        )
        session.add(m)
        await session.commit()
        chat_id = chat.id
        user_id = user.id

    repo = MessageRepository(db_manager)
    result = await repo.get_messages_by_chat_id_and_period(
        chat_id=chat_id, start_date=start, end_date=end
    )
    assert len(result) >= 1
    result_tracked = await repo.get_messages_by_chat_id_and_period(
        chat_id=chat_id,
        start_date=start,
        end_date=end,
        tracked_user_ids=[user_id],
    )
    assert len(result_tracked) >= 1


@pytest.mark.asyncio
async def test_get_max_message_id(db_manager: Any) -> None:
    """Максимальный id сообщения в чате."""
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_msg_max", title="Msg Max")
        user = User(tg_id="msg_m", username="msg_m")
        session.add_all([chat, user])
        await session.flush()
        m = ChatMessage(
            chat_id=chat.id,
            user_id=user.id,
            message_id="mm1",
            message_type="text",
            content_type="text",
            created_at=datetime.now(timezone.utc),
        )
        session.add(m)
        await session.commit()
        chat_id = chat.id

    repo = MessageRepository(db_manager)
    max_id = await repo.get_max_message_id(chat_id)
    assert max_id is not None
    assert max_id >= 1


@pytest.mark.asyncio
async def test_get_max_message_id_empty_chat(db_manager: Any) -> None:
    """get_max_message_id для чата без сообщений."""
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_msg_em", title="Msg Em")
        session.add(chat)
        await session.commit()
        chat_id = chat.id

    repo = MessageRepository(db_manager)
    assert await repo.get_max_message_id(chat_id) is None


@pytest.mark.asyncio
async def test_count_messages_since(db_manager: Any) -> None:
    """Подсчёт новых текстовых сообщений после last_id."""
    now = datetime.now(timezone.utc)
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_msg_cnt", title="Msg Cnt")
        user = User(tg_id="msg_c", username="msg_c")
        session.add_all([chat, user])
        await session.flush()
        m = ChatMessage(
            chat_id=chat.id,
            user_id=user.id,
            message_id="mc1",
            message_type="text",
            content_type="text",
            text="x",
            created_at=now,
        )
        session.add(m)
        await session.commit()
        chat_id = chat.id
        last_id = 0

    repo = MessageRepository(db_manager)
    count = await repo.count_messages_since(chat_id=chat_id, last_id=last_id)
    assert count >= 1


@pytest.mark.asyncio
async def test_bulk_create_messages_empty(db_manager: Any) -> None:
    """bulk_create_messages с пустым списком возвращает 0."""
    repo = MessageRepository(db_manager)
    assert await repo.bulk_create_messages([]) == 0


@pytest.mark.asyncio
async def test_bulk_create_messages(db_manager: Any) -> None:
    """Массовое создание сообщений."""
    now = datetime.now(timezone.utc)
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_msg_bulk", title="Msg Bulk")
        user = User(tg_id="msg_b", username="msg_b")
        session.add_all([chat, user])
        await session.commit()
        chat_id = chat.id
        user_id = user.id

    repo = MessageRepository(db_manager)
    dtos = [
        BufferedMessageDTO(
            chat_id=chat_id,
            user_id=user_id,
            message_id="bulk_1",
            message_type="text",
            content_type="text",
            text="Bulk message",
            created_at=now,
        ),
    ]
    count = await repo.bulk_create_messages(dtos)
    assert count == 1


@pytest.mark.asyncio
async def test_get_daily_top_users(db_manager: Any) -> None:
    """Топ пользователей за период."""
    now = datetime.now(timezone.utc)
    start = now - timedelta(days=1)
    end = now + timedelta(days=1)
    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-100_msg_top", title="Msg Top")
        user = User(tg_id="msg_t", username="msg_t")
        session.add_all([chat, user])
        await session.flush()
        for i in range(2):
            m = ChatMessage(
                chat_id=chat.id,
                user_id=user.id,
                message_id=f"mt{i}",
                message_type="text",
                content_type="text",
                created_at=now,
            )
            session.add(m)
        await session.commit()
        chat_id = chat.id

    repo = MessageRepository(db_manager)
    top = await repo.get_daily_top_users(
        chat_id=chat_id, start_date=start, end_date=end, limit=10
    )
    assert len(top) >= 1
    assert top[0].message_count >= 2
