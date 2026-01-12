from datetime import datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import select

from dto.buffer import BufferedMessageReplyDTO
from models import ChatMessage, ChatSession, MessageReply, User
from repositories.message_reply_repository import MessageReplyRepository


@pytest.mark.asyncio
async def test_get_replies_by_period_date(db_manager: Any) -> None:
    """Тестирует получение ответов пользователя за период."""
    # Arrange
    repo = MessageReplyRepository(db_manager)
    now = datetime.now()
    start = now - timedelta(hours=1)
    end = now + timedelta(hours=1)

    async with db_manager.session() as session:
        user = User(tg_id="u_period", username="user_period")
        chat = ChatSession(chat_id="-period", title="Chat Period")
        session.add_all([user, chat])
        await session.flush()

        # Создаем сообщения, на которые будут ответы (для соблюдения FK)
        m1 = ChatMessage(
            chat_id=chat.id,
            user_id=user.id,
            message_id="m1_p",
            message_type="text",
            content_type="text",
        )
        m2 = ChatMessage(
            chat_id=chat.id,
            user_id=user.id,
            message_id="m2_p",
            message_type="text",
            content_type="text",
        )
        m3 = ChatMessage(
            chat_id=chat.id,
            user_id=user.id,
            message_id="m3_p",
            message_type="text",
            content_type="text",
        )
        session.add_all([m1, m2, m3])
        await session.flush()

        # 3 ответа: до, во время, после
        r1 = MessageReply(
            chat_id=chat.id,
            reply_user_id=user.id,
            reply_message_id=m1.id,
            original_message_url="url1",
            response_time_seconds=10,
            created_at=now - timedelta(hours=2),
        )
        r2 = MessageReply(
            chat_id=chat.id,
            reply_user_id=user.id,
            reply_message_id=m2.id,
            original_message_url="url2",
            response_time_seconds=20,
            created_at=now,
        )
        r3 = MessageReply(
            chat_id=chat.id,
            reply_user_id=user.id,
            reply_message_id=m3.id,
            original_message_url="url3",
            response_time_seconds=30,
            created_at=now + timedelta(hours=2),
        )
        session.add_all([r1, r2, r3])
        await session.commit()
        user_id = user.id

    # Act
    replies = await repo.get_replies_by_period_date(user_id, start, end)

    # Assert
    assert len(replies) == 1
    assert replies[0].original_message_url == "url2"


@pytest.mark.asyncio
async def test_get_replies_by_chat_id_and_period(db_manager: Any) -> None:
    """Тестирует получение ответов в конкретном чате за период."""
    # Arrange
    repo = MessageReplyRepository(db_manager)
    now = datetime.now()

    async with db_manager.session() as session:
        u1 = User(tg_id="u_chat1", username="user_chat1")
        u2 = User(tg_id="u_chat2", username="user_chat2")
        c1 = ChatSession(chat_id="-chat1", title="Chat 1")
        c2 = ChatSession(chat_id="-chat2", title="Chat 2")
        session.add_all([u1, u2, c1, c2])
        await session.flush()

        m1 = ChatMessage(
            chat_id=c1.id,
            user_id=u1.id,
            message_id="m1_c",
            message_type="text",
            content_type="text",
        )
        m2 = ChatMessage(
            chat_id=c2.id,
            user_id=u1.id,
            message_id="m2_c",
            message_type="text",
            content_type="text",
        )
        m3 = ChatMessage(
            chat_id=c1.id,
            user_id=u2.id,
            message_id="m3_c",
            message_type="text",
            content_type="text",
        )
        session.add_all([m1, m2, m3])
        await session.flush()

        # Ответы в разных чатах
        r1 = MessageReply(
            chat_id=c1.id,
            reply_user_id=u1.id,
            reply_message_id=m1.id,
            original_message_url="url1_c",
            response_time_seconds=10,
            created_at=now,
        )
        r2 = MessageReply(
            chat_id=c2.id,
            reply_user_id=u1.id,
            reply_message_id=m2.id,
            original_message_url="url2_c",
            response_time_seconds=20,
            created_at=now,
        )
        # Ответ от другого пользователя в c1
        r3 = MessageReply(
            chat_id=c1.id,
            reply_user_id=u2.id,
            reply_message_id=m3.id,
            original_message_url="url3_c",
            response_time_seconds=30,
            created_at=now,
        )
        session.add_all([r1, r2, r3])
        await session.commit()
        chat1_id, user1_id = c1.id, u1.id

    # Act
    # 1. Просто по чату
    all_chat_replies = await repo.get_replies_by_chat_id_and_period(
        chat1_id, now - timedelta(minutes=1), now + timedelta(minutes=1)
    )
    # 2. По чату + отслеживаемый пользователь
    filtered_replies = await repo.get_replies_by_chat_id_and_period(
        chat1_id,
        now - timedelta(minutes=1),
        now + timedelta(minutes=1),
        tracked_user_ids=[user1_id],
    )

    # Assert
    assert len(all_chat_replies) == 2
    assert len(filtered_replies) == 1
    assert filtered_replies[0].reply_user_id == user1_id


@pytest.mark.asyncio
async def test_get_replies_by_period_date_and_chats(db_manager: Any) -> None:
    """Тестирует фильтрацию ответов по списку чатов."""
    # Arrange
    repo = MessageReplyRepository(db_manager)
    now = datetime.now()

    async with db_manager.session() as session:
        u1 = User(tg_id="u_chats_list", username="user_chats_list")
        c1 = ChatSession(chat_id="-list1", title="A")
        c2 = ChatSession(chat_id="-list2", title="B")
        c3 = ChatSession(chat_id="-list3", title="C")
        session.add_all([u1, c1, c2, c3])
        await session.flush()

        for idx, c in enumerate([c1, c2, c3]):
            m = ChatMessage(
                chat_id=c.id,
                user_id=u1.id,
                message_id=f"mlist_{idx}",
                message_type="text",
                content_type="text",
            )
            session.add(m)
            await session.flush()
            session.add(
                MessageReply(
                    chat_id=c.id,
                    reply_user_id=u1.id,
                    reply_message_id=m.id,
                    original_message_url=f"urllist_{idx}",
                    response_time_seconds=10,
                    created_at=now,
                )
            )
        await session.commit()
        user_id = u1.id
        target_chats = [c1.id, c2.id]

    # Act
    replies = await repo.get_replies_by_period_date_and_chats(
        user_id,
        now - timedelta(minutes=1),
        now + timedelta(minutes=1),
        chat_ids=target_chats,
    )

    # Assert
    assert len(replies) == 2
    for r in replies:
        assert r.chat_id in target_chats


@pytest.mark.asyncio
async def test_bulk_create_replies(db_manager: Any) -> None:
    """Тестирует массовое создание ответов со связыванием через ChatMessage."""
    # Arrange
    repo = MessageReplyRepository(db_manager)
    now = datetime.now()

    async with db_manager.session() as session:
        chat = ChatSession(chat_id="-bulk_reply", title="Bulk Chat")
        user = User(tg_id="u_bulk", username="user_bulk")
        session.add_all([chat, user])
        await session.flush()

        # Создаем сообщение, на которое будет ссылаться reply
        msg = ChatMessage(
            chat_id=chat.id,
            user_id=user.id,
            message_id="msg_bulk_100",
            message_type="text",
            content_type="text",
            created_at=now,
        )
        session.add(msg)
        await session.commit()
        chat_db_id, user_db_id, msg_db_id = chat.id, user.id, msg.id

    # Подготавливаем DTO
    dtos = [
        # 1. Валидный (сообщение существует)
        BufferedMessageReplyDTO(
            chat_id=chat_db_id,
            original_message_url="url_bulk_ok",
            reply_message_id_str="msg_bulk_100",  # Ищем по этому полю
            reply_user_id=user_db_id,
            response_time_seconds=15,
            created_at=now,
            original_message_date=now,
            reply_message_date=now,
        ),
        # 2. Невалидный (сообщения нет в базе)
        BufferedMessageReplyDTO(
            chat_id=chat_db_id,
            original_message_url="url_bulk_fail",
            reply_message_id_str="non_existent_msg",
            reply_user_id=user_db_id,
            response_time_seconds=5,
            created_at=now,
            original_message_date=now,
            reply_message_date=now,
        ),
    ]

    # Act
    inserted_count = await repo.bulk_create_replies(dtos)

    # Assert
    assert inserted_count == 1

    # Проверяем в базе
    async with db_manager.session() as session:
        result = await session.execute(
            select(MessageReply).where(
                MessageReply.original_message_url == "url_bulk_ok"
            )
        )
        reply = result.scalar_one()
        assert reply.reply_message_id == msg_db_id
        assert reply.response_time_seconds == 15


@pytest.mark.asyncio
async def test_reply_error_handling_graceful(db_manager: Any) -> None:
    """Проверяет, что методы репозитория корректно обрабатывают пустые данные."""
    # Arrange
    repo = MessageReplyRepository(db_manager)

    # Act & Assert
    # 1. Bulk create с пустым списком
    assert await repo.bulk_create_replies([]) == 0

    # 2. Запрос по несуществующему пользователю
    replies = await repo.get_replies_by_period_date(
        999999, datetime.now(), datetime.now()
    )
    assert replies == []
