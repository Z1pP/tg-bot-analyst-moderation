"""Тесты для MessageTemplateRepository."""

from typing import Any

import pytest

from models import ChatSession, MessageTemplate, TemplateCategory, User
from repositories.template_repository import MessageTemplateRepository


@pytest.mark.asyncio
async def test_create_template(db_manager: Any) -> None:
    """Создание шаблона."""
    async with db_manager.session() as session:
        user = User(tg_id="tpl_c", username="tpl_c")
        chat = ChatSession(chat_id="-100_tpl_c", title="Tpl C")
        cat = TemplateCategory(name="CatCreate", sort_order=0)
        session.add_all([user, chat, cat])
        await session.commit()
        author_id, chat_id, category_id = user.id, chat.id, cat.id

    repo = MessageTemplateRepository(db_manager)
    t = await repo.create_template(
        title="Test Template",
        content="Hello",
        category_id=category_id,
        author_id=author_id,
        chat_id=chat_id,
    )
    assert t.id is not None
    assert t.title == "Test Template"
    assert t.content == "Hello"
    assert t.usage_count == 0


@pytest.mark.asyncio
async def test_get_template_by_id(db_manager: Any) -> None:
    """Получение шаблона по id."""
    async with db_manager.session() as session:
        user = User(tg_id="tpl_g", username="tpl_g")
        cat = TemplateCategory(name="CatGet", sort_order=0)
        session.add_all([user, cat])
        await session.flush()
        t = MessageTemplate(
            title="Get Me",
            content="Content",
            category_id=cat.id,
            author_id=user.id,
        )
        session.add(t)
        await session.commit()
        tid = t.id

    repo = MessageTemplateRepository(db_manager)
    found = await repo.get_template_by_id(tid)
    assert found is not None
    assert found.title == "Get Me"


@pytest.mark.asyncio
async def test_get_template_by_id_not_found(db_manager: Any) -> None:
    """get_template_by_id возвращает None для несуществующего id."""
    repo = MessageTemplateRepository(db_manager)
    assert await repo.get_template_by_id(99999) is None


@pytest.mark.asyncio
async def test_get_templates_count(db_manager: Any) -> None:
    """Подсчёт шаблонов с фильтрами."""
    async with db_manager.session() as session:
        user = User(tg_id="tpl_cnt", username="tpl_cnt")
        cat = TemplateCategory(name="CatCnt", sort_order=0)
        session.add_all([user, cat])
        await session.flush()
        t1 = MessageTemplate(
            title="T1", content="C1", category_id=cat.id, author_id=user.id
        )
        t2 = MessageTemplate(
            title="T2", content="C2", category_id=cat.id, author_id=user.id
        )
        session.add_all([t1, t2])
        await session.commit()
        category_id = cat.id

    repo = MessageTemplateRepository(db_manager)
    count = await repo.get_templates_count(category_id=category_id)
    assert count >= 2


@pytest.mark.asyncio
async def test_get_templates_paginated(db_manager: Any) -> None:
    """Пагинация шаблонов."""
    async with db_manager.session() as session:
        user = User(tg_id="tpl_pag", username="tpl_pag")
        cat = TemplateCategory(name="CatPag", sort_order=0)
        session.add_all([user, cat])
        await session.flush()
        for i in range(3):
            t = MessageTemplate(
                title=f"Pag{i}",
                content="x",
                category_id=cat.id,
                author_id=user.id,
            )
            session.add(t)
        await session.commit()
        category_id = cat.id

    repo = MessageTemplateRepository(db_manager)
    page = await repo.get_templates_paginated(
        offset=0, limit=2, category_id=category_id
    )
    assert len(page) <= 2


@pytest.mark.asyncio
async def test_get_templates_by_query(db_manager: Any) -> None:
    """Поиск шаблонов по подстроке в названии."""
    async with db_manager.session() as session:
        user = User(tg_id="tpl_q", username="tpl_q")
        cat = TemplateCategory(name="CatQ", sort_order=0)
        session.add_all([user, cat])
        await session.flush()
        t = MessageTemplate(
            title="UniqueSearchTitle",
            content="x",
            category_id=cat.id,
            author_id=user.id,
        )
        session.add(t)
        await session.commit()

    repo = MessageTemplateRepository(db_manager)
    result = await repo.get_templates_by_query("UniqueSearch")
    assert any(t.title == "UniqueSearchTitle" for t in result)


@pytest.mark.asyncio
async def test_delete_template(db_manager: Any) -> None:
    """Удаление шаблона."""
    async with db_manager.session() as session:
        user = User(tg_id="tpl_d", username="tpl_d")
        cat = TemplateCategory(name="CatDel", sort_order=0)
        session.add_all([user, cat])
        await session.flush()
        t = MessageTemplate(
            title="ToDelete",
            content="x",
            category_id=cat.id,
            author_id=user.id,
        )
        session.add(t)
        await session.commit()
        tid = t.id

    repo = MessageTemplateRepository(db_manager)
    ok = await repo.delete_template(tid)
    assert ok is True
    assert await repo.get_template_by_id(tid) is None


@pytest.mark.asyncio
async def test_delete_template_not_found(db_manager: Any) -> None:
    """delete_template возвращает False для несуществующего id."""
    repo = MessageTemplateRepository(db_manager)
    assert await repo.delete_template(99999) is False


@pytest.mark.asyncio
async def test_update_template_title(db_manager: Any) -> None:
    """Обновление названия шаблона."""
    async with db_manager.session() as session:
        user = User(tg_id="tpl_ut", username="tpl_ut")
        cat = TemplateCategory(name="CatUT", sort_order=0)
        session.add_all([user, cat])
        await session.flush()
        t = MessageTemplate(
            title="OldTitle",
            content="x",
            category_id=cat.id,
            author_id=user.id,
        )
        session.add(t)
        await session.commit()
        tid = t.id

    repo = MessageTemplateRepository(db_manager)
    ok = await repo.update_template_title(tid, "NewTitle")
    assert ok is True
    found = await repo.get_template_by_id(tid)
    assert found is not None
    assert found.title == "NewTitle"
