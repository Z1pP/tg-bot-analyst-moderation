from datetime import datetime, timedelta
from typing import Any

import pytest

from constants.enums import UserRole
from models import ChatMessage, MessageReaction, User
from repositories.user_repository import UserRepository


@pytest.mark.asyncio
async def test_create_user(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)
    tg_id = "123456789"
    username = "test_user"

    # Act
    user = await repo.create_user(tg_id=tg_id, username=username, role=UserRole.USER)

    # Assert
    assert user.id is not None
    assert user.tg_id == tg_id
    assert user.username == username
    assert user.role == UserRole.USER


@pytest.mark.asyncio
async def test_get_user_by_tg_id(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)
    tg_id = "987654321"
    async with db_manager.session() as session:
        user = User(tg_id=tg_id, username="find_me", role=UserRole.USER)
        session.add(user)
        await session.commit()

    # Act
    found_user = await repo.get_user_by_tg_id(tg_id)

    # Assert
    assert found_user is not None
    assert found_user.tg_id == tg_id
    assert found_user.username == "find_me"


@pytest.mark.asyncio
async def test_total_active_users(db_manager: Any) -> None:
    # Arrange
    from models import ChatSession

    repo = UserRepository(db_manager)
    tg_chat_id = "-100123456789"
    now = datetime.now()
    start_date = now - timedelta(days=1)
    end_date = now + timedelta(days=1)

    async with db_manager.session() as session:
        # Create ChatSession first
        chat = ChatSession(chat_id=tg_chat_id, title="Test Chat")
        session.add(chat)
        await session.flush()
        chat_db_id: int = chat.id

        # User 1: only messages
        u1 = User(tg_id="u1_active", username="user1")
        session.add(u1)
        await session.flush()
        m1 = ChatMessage(
            chat_id=chat_db_id,
            user_id=u1.id,
            message_id="m1",
            message_type="text",
            content_type="text",
            created_at=now,
        )
        session.add(m1)

        # User 2: only reactions
        from constants.enums import ReactionAction

        u2 = User(tg_id="u2_active", username="user2")
        session.add(u2)
        await session.flush()
        r1 = MessageReaction(
            chat_id=chat_db_id,
            user_id=u2.id,
            message_id="m_ext",
            action=ReactionAction.ADDED,
            emoji="👍",
            message_url="url",
            created_at=now,
        )
        session.add(r1)

        # User 3: both (should be counted once)
        u3 = User(tg_id="u3_active", username="user3")
        session.add(u3)
        await session.flush()
        m2 = ChatMessage(
            chat_id=chat_db_id,
            user_id=u3.id,
            message_id="m2",
            message_type="text",
            content_type="text",
            created_at=now,
        )
        r2 = MessageReaction(
            chat_id=chat_db_id,
            user_id=u3.id,
            message_id="m2",
            action=ReactionAction.ADDED,
            emoji="🔥",
            message_url="url",
            created_at=now,
        )
        session.add_all([m2, r2])

        # User 4: message in another chat (should not be counted)
        chat2 = ChatSession(chat_id="-999_active", title="Another Chat")
        session.add(chat2)
        await session.flush()
        u4 = User(tg_id="u4_active", username="user4")
        session.add(u4)
        await session.flush()
        m3 = ChatMessage(
            chat_id=chat2.id,
            user_id=u4.id,
            message_id="m3",
            message_type="text",
            content_type="text",
            created_at=now,
        )
        session.add(m3)

        await session.commit()

    # Act
    count = await repo.total_active_users(chat_db_id, start_date, end_date)

    # Assert
    assert count == 3


@pytest.mark.asyncio
async def test_get_user_by_id(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="by_id_type", username="by_id_user")
        session.add(user)
        await session.commit()
        user_id: int = user.id

    # Act
    found_user = await repo.get_user_by_id(user_id)

    # Assert
    assert found_user is not None
    assert found_user.id == user_id
    assert found_user.username == "by_id_user"


@pytest.mark.asyncio
async def test_get_user_by_username(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)
    username = "unique_username_type"
    async with db_manager.session() as session:
        user = User(tg_id="by_uname_type", username=username)
        session.add(user)
        await session.commit()

    # Act
    found_user = await repo.get_user_by_username(username)

    # Assert
    assert found_user is not None
    assert found_user.username == username


@pytest.mark.asyncio
async def test_update_user(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="update_me_type", username="old_name")
        session.add(user)
        await session.commit()
        user_id: int = user.id

    # Act
    new_name = "new_name"
    updated_user = await repo.update_user(user_id, new_name)

    # Assert
    assert updated_user.username == new_name

    # Verify in DB
    refreshed_user = await repo.get_user_by_id(user_id)
    assert refreshed_user is not None
    assert refreshed_user.username == new_name


@pytest.mark.asyncio
async def test_update_user_language(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="lang_me_type", username="lang_user", language="ru")
        session.add(user)
        await session.commit()
        user_id: int = user.id

    # Act
    updated_user = await repo.update_user_language(user_id, "en")

    # Assert
    assert updated_user.language == "en"


@pytest.mark.asyncio
async def test_update_user_role(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="role_me_type", username="role_user", role=UserRole.USER)
        session.add(user)
        await session.commit()
        user_id: int = user.id

    # Act
    updated_user = await repo.update_user_role(user_id, UserRole.MODERATOR)

    # Assert
    assert updated_user.role == UserRole.MODERATOR


@pytest.mark.asyncio
async def test_delete_user(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="delete_me_type", username="delete_user")
        session.add(user)
        await session.commit()
        user_id: int = user.id

    # Act
    deleted = await repo.delete_user(user_id)

    # Assert
    assert deleted is True
    found_user = await repo.get_user_by_id(user_id)
    assert found_user is None


@pytest.mark.asyncio
async def test_delete_non_existent_user(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)

    # Act
    deleted = await repo.delete_user(99999)

    # Assert
    assert deleted is False


@pytest.mark.asyncio
async def test_create_user_validation(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)

    # Act & Assert
    with pytest.raises(ValueError, match="tg_id или username должны быть указаны"):
        await repo.create_user(tg_id=None, username=None)


@pytest.mark.asyncio
async def test_get_all_moderators(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)
    async with db_manager.session() as session:
        m1 = User(tg_id="m1_mod_type", username="mod1_all", role=UserRole.MODERATOR)
        m2 = User(tg_id="m2_mod_type", username="mod2_all", role=UserRole.MODERATOR)
        u1 = User(tg_id="u1_mod_type", username="user1_all", role=UserRole.USER)
        session.add_all([m1, m2, u1])
        await session.commit()

    # Act
    moderators = await repo.get_all_moderators()

    # Assert
    assert len(moderators) >= 2
    usernames = [m.username for m in moderators]
    assert "mod1_all" in usernames
    assert "mod2_all" in usernames
    assert "user1_all" not in usernames


@pytest.mark.asyncio
async def test_get_all_admins(db_manager: Any) -> None:
    # Arrange
    repo = UserRepository(db_manager)
    async with db_manager.session() as session:
        a1 = User(
            tg_id="a1_all_type",
            username="admin1_all",
            role=UserRole.ADMIN,
            is_active=True,
        )
        a2 = User(
            tg_id="a2_all_type",
            username="admin2_all",
            role=UserRole.ADMIN,
            is_active=True,
        )
        a3 = User(
            tg_id="a3_all_type",
            username="admin3_all",
            role=UserRole.ADMIN,
            is_active=False,
        )  # inactive
        m1 = User(
            tg_id="m1_all_adm_type", username="mod1_all_adm", role=UserRole.MODERATOR
        )
        session.add_all([a1, a2, a3, m1])
        await session.commit()

    # Act
    admins = await repo.get_all_admins()

    # Assert
    assert len(admins) >= 2
    usernames = [a.username for a in admins]
    assert "admin1_all" in usernames
    assert "admin2_all" in usernames
    assert "admin3_all" not in usernames
    assert "mod1_all_adm" not in usernames


@pytest.mark.asyncio
async def test_get_tracked_users_for_admin(db_manager: Any) -> None:
    # Arrange
    from models import admin_user_tracking

    repo = UserRepository(db_manager)
    admin_tg_id = "admin_tr_unique_type"
    async with db_manager.session() as session:
        admin = User(tg_id=admin_tg_id, username="admin_tr", role=UserRole.ADMIN)
        u1 = User(tg_id="u1_tr_unique_type", username="user1_tr")
        u2 = User(tg_id="u2_tr_unique_type", username="user2_tr")
        u3 = User(tg_id="u3_tr_unique_type", username="user3_tr")
        session.add_all([admin, u1, u2, u3])
        await session.flush()

        # Admin tracks u1 and u2, but not u3
        await session.execute(
            admin_user_tracking.insert().values(
                [
                    {"admin_id": admin.id, "tracked_user_id": u1.id},
                    {"admin_id": admin.id, "tracked_user_id": u2.id},
                ]
            )
        )
        await session.commit()

    # Act
    tracked_users = await repo.get_tracked_users_for_admin(admin_tg_id)

    # Assert
    assert len(tracked_users) == 2
    usernames = [u.username for u in tracked_users]
    assert "user1_tr" in usernames
    assert "user2_tr" in usernames
    assert "user3_tr" not in usernames


@pytest.mark.asyncio
async def test_get_admins_for_chat(db_manager: Any) -> None:
    # Arrange
    from models import AdminChatAccess, ChatSession

    repo = UserRepository(db_manager)
    chat_tg_id = "chat_admins_test_type"
    async with db_manager.session() as session:
        chat = ChatSession(chat_id=chat_tg_id, title="Admin Chat")
        a1 = User(tg_id="a1_chat_type", username="admin1_chat", role=UserRole.ADMIN)
        a2 = User(tg_id="a2_chat_type", username="admin2_chat", role=UserRole.ADMIN)
        u1 = User(tg_id="u1_chat_type", username="user1_chat", role=UserRole.USER)
        session.add_all([chat, a1, a2, u1])
        await session.flush()

        # a1 and a2 have access to chat
        access1 = AdminChatAccess(admin_id=a1.id, chat_id=chat.id)
        access2 = AdminChatAccess(admin_id=a2.id, chat_id=chat.id)
        session.add_all([access1, access2])
        await session.commit()

    # Act
    admins = await repo.get_admins_for_chat(chat_tg_id)

    # Assert
    assert admins is not None
    assert len(admins) == 2
    usernames = [a.username for a in admins]
    assert "admin1_chat" in usernames
    assert "admin2_chat" in usernames
    assert "user1_chat" not in usernames
