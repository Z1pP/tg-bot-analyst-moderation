"""Тесты для UserChatStatusRepository."""

from typing import Any

import pytest

from models import ChatSession, User, UserChatStatus
from repositories.user_chat_status_repository import UserChatStatusRepository


@pytest.mark.asyncio
async def test_get_status_not_found(db_manager: Any) -> None:
    """get_status возвращает None для несуществующей пары user_id/chat_id."""
    repo = UserChatStatusRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="ucs_1", username="ucs_user")
        chat = ChatSession(chat_id="-100_ucs", title="UCS Chat")
        session.add_all([user, chat])
        await session.commit()
        user_id, chat_id = user.id, chat.id

    result = await repo.get_status(user_id=user_id, chat_id=chat_id)
    assert result is None


@pytest.mark.asyncio
async def test_get_or_create_creates(db_manager: Any) -> None:
    """get_or_create создаёт запись и возвращает (status, True)."""
    repo = UserChatStatusRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="ucs_create", username="ucs_c")
        chat = ChatSession(chat_id="-100_ucs_c", title="UCS Create")
        session.add_all([user, chat])
        await session.commit()
        user_id, chat_id = user.id, chat.id

    status, created = await repo.get_or_create(user_id=user_id, chat_id=chat_id)
    assert status.id is not None
    assert status.user_id == user_id
    assert status.chat_id == chat_id
    assert created is True


@pytest.mark.asyncio
async def test_get_or_create_returns_existing(db_manager: Any) -> None:
    """get_or_create возвращает существующую запись и (status, False)."""
    repo = UserChatStatusRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="ucs_exist", username="ucs_e")
        chat = ChatSession(chat_id="-100_ucs_e", title="UCS Exist")
        session.add_all([user, chat])
        await session.flush()
        status = UserChatStatus(user_id=user.id, chat_id=chat.id, is_banned=True)
        session.add(status)
        await session.commit()
        user_id, chat_id = user.id, chat.id

    status, created = await repo.get_or_create(user_id=user_id, chat_id=chat_id)
    assert status.id is not None
    assert status.is_banned is True
    assert created is False


@pytest.mark.asyncio
async def test_get_or_create_with_defaults(db_manager: Any) -> None:
    """get_or_create с defaults задаёт поля при создании."""
    repo = UserChatStatusRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="ucs_def", username="ucs_d")
        chat = ChatSession(chat_id="-100_ucs_d", title="UCS Def")
        session.add_all([user, chat])
        await session.commit()
        user_id, chat_id = user.id, chat.id

    status, created = await repo.get_or_create(
        user_id=user_id,
        chat_id=chat_id,
        defaults={"is_muted": True},
    )
    assert created is True
    assert status.is_muted is True


@pytest.mark.asyncio
async def test_get_status_found(db_manager: Any) -> None:
    """get_status возвращает запись при её наличии."""
    repo = UserChatStatusRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="ucs_get", username="ucs_g")
        chat = ChatSession(chat_id="-100_ucs_g", title="UCS Get")
        session.add_all([user, chat])
        await session.flush()
        status = UserChatStatus(user_id=user.id, chat_id=chat.id)
        session.add(status)
        await session.commit()
        user_id, chat_id = user.id, chat.id

    result = await repo.get_status(user_id=user_id, chat_id=chat_id)
    assert result is not None
    assert result.user_id == user_id
    assert result.chat_id == chat_id


@pytest.mark.asyncio
async def test_update_status(db_manager: Any) -> None:
    """update_status обновляет поля и возвращает обновлённый объект."""
    repo = UserChatStatusRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="ucs_upd", username="ucs_u")
        chat = ChatSession(chat_id="-100_ucs_u", title="UCS Upd")
        session.add_all([user, chat])
        await session.flush()
        status = UserChatStatus(user_id=user.id, chat_id=chat.id)
        session.add(status)
        await session.commit()
        user_id, chat_id = user.id, chat.id

    updated = await repo.update_status(user_id=user_id, chat_id=chat_id, is_banned=True)
    assert updated is not None
    assert updated.is_banned is True

    got = await repo.get_status(user_id=user_id, chat_id=chat_id)
    assert got is not None
    assert got.is_banned is True


@pytest.mark.asyncio
async def test_update_status_not_found(db_manager: Any) -> None:
    """update_status возвращает None для несуществующей записи."""
    repo = UserChatStatusRepository(db_manager)
    async with db_manager.session() as session:
        user = User(tg_id="ucs_nf", username="ucs_nf")
        chat = ChatSession(chat_id="-100_ucs_nf", title="UCS NF")
        session.add_all([user, chat])
        await session.commit()
        user_id, chat_id = user.id, chat.id

    result = await repo.update_status(user_id=user_id, chat_id=chat_id, is_muted=True)
    assert result is None
