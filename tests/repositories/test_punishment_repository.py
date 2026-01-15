from datetime import datetime, timedelta
from typing import Any

import pytest
from sqlalchemy import delete, select

from constants.punishment import PunishmentType
from models import (
    ChatMessage,
    ChatSession,
    ChatSettings,
    MessageReply,
    MessageTemplate,
    Punishment,
    TemplateCategory,
    TemplateMedia,
    User,
)
from repositories.punishment_repository import PunishmentRepository


@pytest.fixture(autouse=True)
async def cleanup(db_manager: Any):
    """Очистка таблиц перед каждым тестом."""
    async with db_manager.session() as session:
        # Удаляем в порядке зависимости (сначала те, кто ссылается)
        await session.execute(delete(TemplateMedia))
        await session.execute(delete(MessageTemplate))
        await session.execute(delete(TemplateCategory))
        await session.execute(delete(MessageReply))
        await session.execute(delete(ChatMessage))
        await session.execute(delete(ChatSettings))
        await session.execute(delete(Punishment))
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
async def test_create_punishment(db_manager: Any) -> None:
    """Тестирует создание наказания."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "123", "test_user")
        chat = await create_test_chat(session, "-1001", "Test Chat")

        repo = PunishmentRepository(db_manager)
        punishment = Punishment(
            user_id=user.id,
            chat_id=chat.id,
            step=1,
            punishment_type=PunishmentType.WARNING,
        )

        # Act
        created = await repo.create_punishment(punishment)

        # Assert
        assert created.id is not None
        assert created.user_id == user.id
        assert created.chat_id == chat.id
        assert created.step == 1
        assert created.punishment_type == PunishmentType.WARNING


@pytest.mark.asyncio
async def test_count_punishments(db_manager: Any) -> None:
    """Тестирует подсчет наказаний."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "123", "test_user")
        chat1 = await create_test_chat(session, "-1001", "Chat 1")
        chat2 = await create_test_chat(session, "-1002", "Chat 2")

        repo = PunishmentRepository(db_manager)

        # Add punishments
        p1 = Punishment(
            user_id=user.id,
            chat_id=chat1.id,
            step=1,
            punishment_type=PunishmentType.WARNING,
        )
        p2 = Punishment(
            user_id=user.id,
            chat_id=chat1.id,
            step=2,
            punishment_type=PunishmentType.MUTE,
        )
        p3 = Punishment(
            user_id=user.id,
            chat_id=chat2.id,
            step=1,
            punishment_type=PunishmentType.WARNING,
        )

        await repo.create_punishment(p1)
        await repo.create_punishment(p2)
        await repo.create_punishment(p3)

        # Act & Assert
        assert await repo.count_punishments(user.id) == 3
        assert await repo.count_punishments(user.id, chat1.id) == 2
        assert await repo.count_punishments(user.id, chat2.id) == 1
        assert await repo.count_punishments(999) == 0


@pytest.mark.asyncio
async def test_delete_user_punishments(db_manager: Any) -> None:
    """Тестирует удаление всех наказаний пользователя в чате."""
    async with db_manager.session() as session:
        user1 = await create_test_user(session, "1", "user1")
        user2 = await create_test_user(session, "2", "user2")
        chat1 = await create_test_chat(session, "-1", "chat1")
        chat2 = await create_test_chat(session, "-2", "chat2")

        repo = PunishmentRepository(db_manager)

        # user1 in chat1 (2 punishments)
        await repo.create_punishment(
            Punishment(
                user_id=user1.id,
                chat_id=chat1.id,
                step=1,
                punishment_type=PunishmentType.WARNING,
            )
        )
        await repo.create_punishment(
            Punishment(
                user_id=user1.id,
                chat_id=chat1.id,
                step=2,
                punishment_type=PunishmentType.WARNING,
            )
        )
        # user1 in chat2 (1 punishment)
        await repo.create_punishment(
            Punishment(
                user_id=user1.id,
                chat_id=chat2.id,
                step=1,
                punishment_type=PunishmentType.WARNING,
            )
        )
        # user2 in chat1 (1 punishment)
        await repo.create_punishment(
            Punishment(
                user_id=user2.id,
                chat_id=chat1.id,
                step=1,
                punishment_type=PunishmentType.WARNING,
            )
        )

        # Act
        deleted = await repo.delete_user_punishments(user1.id, chat1.id)

        # Assert
        assert deleted == 2
        assert await repo.count_punishments(user1.id, chat1.id) == 0
        assert await repo.count_punishments(user1.id, chat2.id) == 1
        assert await repo.count_punishments(user2.id, chat1.id) == 1


@pytest.mark.asyncio
async def test_delete_last_punishment(db_manager: Any) -> None:
    """Тестирует удаление последнего наказания."""
    async with db_manager.session() as session:
        user = await create_test_user(session, "1", "user")
        chat = await create_test_chat(session, "-1", "chat")

        repo = PunishmentRepository(db_manager)

        p1 = Punishment(
            user_id=user.id,
            chat_id=chat.id,
            step=1,
            punishment_type=PunishmentType.WARNING,
        )
        p2 = Punishment(
            user_id=user.id,
            chat_id=chat.id,
            step=2,
            punishment_type=PunishmentType.MUTE,
        )

        await repo.create_punishment(p1)
        # Ensure some time difference if needed, but usually default order is by id/created_at
        await repo.create_punishment(p2)

        # Act
        success = await repo.delete_last_punishment(user.id, chat.id)

        # Assert
        assert success is True
        assert await repo.count_punishments(user.id, chat.id) == 1

        # Check remaining is p1
        async with db_manager.session() as s:
            res = await s.execute(
                select(Punishment).where(Punishment.user_id == user.id)
            )
            remaining = res.scalar_one()
            assert remaining.step == 1

        # Test deletion when none left
        await repo.delete_last_punishment(user.id, chat.id)
        assert await repo.delete_last_punishment(user.id, chat.id) is False


@pytest.mark.asyncio
async def test_get_punishment_counts_by_moderator(db_manager: Any) -> None:
    """Тестирует получение статистики наказаний модератора."""
    async with db_manager.session() as session:
        mod = await create_test_user(session, "1", "mod")
        user = await create_test_user(session, "2", "user")
        chat = await create_test_chat(session, "-1", "chat")

        repo = PunishmentRepository(db_manager)

        now = datetime.now()
        start = now - timedelta(days=1)
        end = now + timedelta(days=1)

        # Punishment within range
        p1 = Punishment(
            user_id=user.id,
            chat_id=chat.id,
            step=1,
            punishment_type=PunishmentType.WARNING,
            punished_by_id=mod.id,
        )
        await repo.create_punishment(p1)

        # Punishment outside range (before)
        async with db_manager.session() as s:
            p2 = Punishment(
                user_id=user.id,
                chat_id=chat.id,
                step=2,
                punishment_type=PunishmentType.BAN,
                punished_by_id=mod.id,
                created_at=now - timedelta(days=5),
            )
            s.add(p2)
            await s.commit()

        # Act
        stats = await repo.get_punishment_counts_by_moderator(mod.id, start, end)

        # Assert
        assert stats["warns"] == 1
        assert stats["bans"] == 0

        # Check with chat_ids filter
        stats_chat = await repo.get_punishment_counts_by_moderator(
            mod.id, start, end, chat_ids=[chat.id]
        )
        assert stats_chat["warns"] == 1

        stats_wrong_chat = await repo.get_punishment_counts_by_moderator(
            mod.id, start, end, chat_ids=[999]
        )
        assert stats_wrong_chat["warns"] == 0


@pytest.mark.asyncio
async def test_get_punishment_counts_by_moderators(db_manager: Any) -> None:
    """Тестирует групповую статистику модераторов."""
    async with db_manager.session() as session:
        mod1 = await create_test_user(session, "1", "mod1")
        mod2 = await create_test_user(session, "2", "mod2")
        user = await create_test_user(session, "3", "user")
        chat = await create_test_chat(session, "-1", "chat")

        repo = PunishmentRepository(db_manager)

        now = datetime.now()
        start = now - timedelta(days=1)
        end = now + timedelta(days=1)

        # Mod1: 2 warns
        await repo.create_punishment(
            Punishment(
                user_id=user.id,
                chat_id=chat.id,
                step=1,
                punishment_type=PunishmentType.WARNING,
                punished_by_id=mod1.id,
            )
        )
        await repo.create_punishment(
            Punishment(
                user_id=user.id,
                chat_id=chat.id,
                step=2,
                punishment_type=PunishmentType.WARNING,
                punished_by_id=mod1.id,
            )
        )

        # Mod2: 1 ban
        await repo.create_punishment(
            Punishment(
                user_id=user.id,
                chat_id=chat.id,
                step=3,
                punishment_type=PunishmentType.BAN,
                punished_by_id=mod2.id,
            )
        )

        # Act
        stats = await repo.get_punishment_counts_by_moderators(
            [mod1.id, mod2.id, 999], start, end
        )

        # Assert
        assert stats[mod1.id]["warns"] == 2
        assert stats[mod1.id]["bans"] == 0
        assert stats[mod2.id]["warns"] == 0
        assert stats[mod2.id]["bans"] == 1
        assert stats[999]["warns"] == 0
        assert stats[999]["bans"] == 0
