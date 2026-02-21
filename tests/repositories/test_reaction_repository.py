from datetime import datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import delete, select

from constants.enums import ReactionAction
from dto.buffer import BufferedReactionDTO
from dto.reaction import MessageReactionDTO
from models import (
    ChatMessage,
    ChatSession,
    ChatSettings,
    MessageReaction,
    MessageReply,
    MessageTemplate,
    Punishment,
    TemplateCategory,
    TemplateMedia,
    User,
)
from repositories.reaction_repository import MessageReactionRepository


@pytest.fixture(autouse=True)
async def cleanup(db_manager: Any):
    """Очистка таблиц перед каждым тестом в правильном порядке."""
    async with db_manager.session() as session:
        await session.execute(delete(TemplateMedia))
        await session.execute(delete(MessageTemplate))
        await session.execute(delete(TemplateCategory))
        await session.execute(delete(MessageReply))
        await session.execute(delete(ChatMessage))
        await session.execute(delete(ChatSettings))
        await session.execute(delete(Punishment))
        await session.execute(delete(MessageReaction))
        await session.execute(delete(ChatSession))
        await session.execute(delete(User))
        await session.commit()


async def create_test_user(session, tg_id: str, username: str) -> User:
    user = User(tg_id=tg_id, username=username)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def create_test_chat(session, chat_id: str, title: str) -> ChatSession:
    chat = ChatSession(chat_id=chat_id, title=title)
    session.add(chat)
    await session.commit()
    await session.refresh(chat)
    return chat


@pytest.mark.asyncio
async def test_add_reaction(db_manager: Any) -> None:
    """Тестирует одиночное добавление реакции."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "1", "user1")
        chat = await create_test_chat(session, "-1", "chat1")

        repo = MessageReactionRepository(db_manager)
        dto = MessageReactionDTO(
            chat_tgid=str(chat.id),
            user_tgid=str(user.id),
            message_id="100",
            action=ReactionAction.ADDED,
            emoji="👍",
            message_url="https://t.me/c/1/100",
        )

        # Act
        reaction = await repo.add_reaction(dto)

        # Assert
        assert reaction.id is not None
        assert reaction.chat_id == chat.id
        assert reaction.user_id == user.id
        assert reaction.emoji == "👍"
        assert reaction.action == ReactionAction.ADDED


@pytest.mark.asyncio
async def test_bulk_add_reactions(db_manager: Any) -> None:
    """Тестирует массовое добавление реакций."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "1", "user1")
        chat = await create_test_chat(session, "-1", "chat1")

        repo = MessageReactionRepository(db_manager)
        dtos = [
            BufferedReactionDTO(
                chat_id=chat.id,
                user_id=user.id,
                message_id="101",
                action=ReactionAction.ADDED.value,
                emoji="❤️",
                message_url="url1",
                created_at=datetime.now(),
            ),
            BufferedReactionDTO(
                chat_id=chat.id,
                user_id=user.id,
                message_id="102",
                action=ReactionAction.ADDED.value,
                emoji="🔥",
                message_url="url2",
                created_at=datetime.now(),
            ),
        ]

        # Act
        count = await repo.bulk_add_reactions(dtos)

        # Assert
        assert count == 2
        async with db_manager.session() as s:
            res = await s.execute(
                select(MessageReaction).where(MessageReaction.chat_id == chat.id)
            )
            reactions = res.scalars().all()
            assert len(reactions) == 2


@pytest.mark.asyncio
async def test_get_reactions_by_chat_and_period(db_manager: Any) -> None:
    """Тестирует получение реакций по чату и периоду."""
    async with db_manager.session() as session:
        user1 = await create_test_user(session, "1", "user1")
        user2 = await create_test_user(session, "2", "user2")
        chat = await create_test_chat(session, "-1", "chat1")

        repo = MessageReactionRepository(db_manager)
        now = datetime.now()

        # In period
        await repo.add_reaction(
            MessageReactionDTO(
                chat_tgid=str(chat.id),
                user_tgid=str(user1.id),
                message_id="1",
                action=ReactionAction.ADDED,
                emoji="👍",
                message_url="u1",
            )
        )
        # Out of period
        async with db_manager.session() as s:
            r2 = MessageReaction(
                chat_id=chat.id,
                user_id=user2.id,
                message_id="2",
                action=ReactionAction.ADDED,
                emoji="👍",
                message_url="u2",
                created_at=now - timedelta(days=5),
            )
            s.add(r2)
            await s.commit()

        start = now - timedelta(days=1)
        end = now + timedelta(days=1)

        # Act
        # 1. All users
        reactions = await repo.get_reactions_by_chat_and_period(chat.id, start, end)
        assert len(reactions) == 1
        assert reactions[0].user_id == user1.id

        # 2. Filtered by tracked users
        reactions_filtered = await repo.get_reactions_by_chat_and_period(
            chat.id, start, end, tracked_user_ids=[user2.id]
        )
        assert len(reactions_filtered) == 0


@pytest.mark.asyncio
async def test_get_daily_top_reactors(db_manager: Any) -> None:
    """Тестирует получение топа реакторов."""
    async with db_manager.session() as session:
        u1 = await create_test_user(session, "1", "user1")
        u2 = await create_test_user(session, "2", "user2")
        chat = await create_test_chat(session, "-1", "chat1")
        repo = MessageReactionRepository(db_manager)

        # u1: 2 reactions
        await repo.add_reaction(
            MessageReactionDTO(
                chat_tgid=str(chat.id),
                user_tgid=str(u1.id),
                message_id="1",
                action=ReactionAction.ADDED,
                emoji="👍",
                message_url="u1",
            )
        )
        await repo.add_reaction(
            MessageReactionDTO(
                chat_tgid=str(chat.id),
                user_tgid=str(u1.id),
                message_id="2",
                action=ReactionAction.ADDED,
                emoji="👍",
                message_url="u2",
            )
        )
        # u2: 1 reaction
        await repo.add_reaction(
            MessageReactionDTO(
                chat_tgid=str(chat.id),
                user_tgid=str(u2.id),
                message_id="3",
                action=ReactionAction.ADDED,
                emoji="🔥",
                message_url="u3",
            )
        )

        # Act
        top = await repo.get_daily_top_reactors(chat.id, date=datetime.now())

        # Assert
        assert len(top) == 2
        assert top[0].user_id == u1.id
        assert top[0].reaction_count == 2
        assert top[1].user_id == u2.id
        assert top[1].reaction_count == 1


@pytest.mark.asyncio
async def test_get_daily_popular_reactions(db_manager: Any) -> None:
    """Тестирует получение популярных реакций."""
    async with db_manager.session() as session:
        u1 = await create_test_user(session, "1", "user1")
        chat = await create_test_chat(session, "-1", "chat1")
        repo = MessageReactionRepository(db_manager)

        # 👍: 2 times
        await repo.add_reaction(
            MessageReactionDTO(
                chat_tgid=str(chat.id),
                user_tgid=str(u1.id),
                message_id="1",
                action=ReactionAction.ADDED,
                emoji="👍",
                message_url="u1",
            )
        )
        await repo.add_reaction(
            MessageReactionDTO(
                chat_tgid=str(chat.id),
                user_tgid=str(u1.id),
                message_id="2",
                action=ReactionAction.ADDED,
                emoji="👍",
                message_url="u2",
            )
        )
        # 🔥: 1 time
        await repo.add_reaction(
            MessageReactionDTO(
                chat_tgid=str(chat.id),
                user_tgid=str(u1.id),
                message_id="3",
                action=ReactionAction.ADDED,
                emoji="🔥",
                message_url="u3",
            )
        )

        # Act
        popular = await repo.get_daily_popular_reactions(chat.id, date=datetime.now())

        # Assert
        assert len(popular) == 2
        assert popular[0].emoji == "👍"
        assert popular[0].count == 2
        assert popular[1].emoji == "🔥"
        assert popular[1].count == 1


@pytest.mark.asyncio
async def test_get_reactions_by_user_and_period_and_chats(db_manager: Any) -> None:
    """Тестирует получение реакций пользователя в нескольких чатах."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "1", "user1")
        chat1 = await create_test_chat(session, "-1", "chat1")
        chat2 = await create_test_chat(session, "-2", "chat2")
        chat3 = await create_test_chat(session, "-3", "chat3")
        repo = MessageReactionRepository(db_manager)

        await repo.add_reaction(
            MessageReactionDTO(
                chat_tgid=str(chat1.id),
                user_tgid=str(user.id),
                message_id="1",
                action=ReactionAction.ADDED,
                emoji="👍",
                message_url="u1",
            )
        )
        await repo.add_reaction(
            MessageReactionDTO(
                chat_tgid=str(chat2.id),
                user_tgid=str(user.id),
                message_id="2",
                action=ReactionAction.ADDED,
                emoji="🔥",
                message_url="u2",
            )
        )
        await repo.add_reaction(
            MessageReactionDTO(
                chat_tgid=str(chat3.id),
                user_tgid=str(user.id),
                message_id="3",
                action=ReactionAction.ADDED,
                emoji="❤️",
                message_url="u3",
            )
        )

        # Act
        reactions = await repo.get_reactions_by_user_and_period_and_chats(
            user.id,
            datetime.now() - timedelta(days=1),
            datetime.now() + timedelta(days=1),
            [chat1.id, chat2.id],
        )

        # Assert
        assert len(reactions) == 2
        chat_ids = [r.chat_id for r in reactions]
        assert chat1.id in chat_ids
        assert chat2.id in chat_ids
        assert chat3.id not in chat_ids
