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


@pytest.mark.asyncio
async def test_update_template_title_not_found(db_manager: Any) -> None:
    """update_template_title для несуществующего id возвращает False."""
    repo = MessageTemplateRepository(db_manager)
    assert await repo.update_template_title(99999, "New") is False


@pytest.mark.asyncio
async def test_get_templates_count_global_only(db_manager: Any) -> None:
    """get_templates_count с global_only=True считает только шаблоны без chat_id."""
    async with db_manager.session() as session:
        user = User(tg_id="tpl_gonly", username="tpl_gonly")
        chat = ChatSession(chat_id="-100_gonly", title="GOnly")
        cat = TemplateCategory(name="CatGOnly", sort_order=0)
        session.add_all([user, chat, cat])
        await session.flush()
        t_global = MessageTemplate(
            title="GlobalT",
            content="x",
            category_id=cat.id,
            author_id=user.id,
            chat_id=None,
        )
        t_chat = MessageTemplate(
            title="ChatT",
            content="x",
            category_id=cat.id,
            author_id=user.id,
            chat_id=chat.id,
        )
        session.add_all([t_global, t_chat])
        await session.commit()

    repo = MessageTemplateRepository(db_manager)
    count = await repo.get_templates_count(global_only=True)
    assert count >= 1


@pytest.mark.asyncio
async def test_get_templates_paginated_global_only(db_manager: Any) -> None:
    """get_templates_paginated с global_only возвращает только глобальные шаблоны."""
    async with db_manager.session() as session:
        user = User(tg_id="tpl_pag_gl", username="tpl_pag_gl")
        cat = TemplateCategory(name="CatPagGl", sort_order=0)
        session.add_all([user, cat])
        await session.flush()
        t = MessageTemplate(
            title="GlobalPag", content="x", category_id=cat.id, author_id=user.id
        )
        session.add(t)
        await session.commit()

    repo = MessageTemplateRepository(db_manager)
    page = await repo.get_templates_paginated(offset=0, limit=10, global_only=True)
    assert all(t.chat_id is None for t in page)


@pytest.mark.asyncio
async def test_get_template_and_increase_usage_count(db_manager: Any) -> None:
    """get_template_and_increase_usage_count находит шаблон и увеличивает usage_count."""
    async with db_manager.session() as session:
        user = User(tg_id="tpl_use", username="tpl_use")
        chat = ChatSession(chat_id="-100_use", title="Use")
        cat = TemplateCategory(name="CatUse", sort_order=0)
        session.add_all([user, chat, cat])
        await session.flush()
        t = MessageTemplate(
            title="UseMe",
            content="C",
            category_id=cat.id,
            author_id=user.id,
            usage_count=0,
        )
        session.add(t)
        await session.commit()
        tid = t.id

    repo = MessageTemplateRepository(db_manager)
    found = await repo.get_template_and_increase_usage_count(tid, "-100_use")
    assert found is not None
    assert found.usage_count == 1
    again = await repo.get_template_by_id(tid)
    assert again is not None
    assert again.usage_count == 1


@pytest.mark.asyncio
async def test_get_template_and_increase_usage_count_not_found(db_manager: Any) -> None:
    """get_template_and_increase_usage_count для несуществующего id возвращает None."""
    repo = MessageTemplateRepository(db_manager)
    assert await repo.get_template_and_increase_usage_count(99999, "-100") is None


@pytest.mark.asyncio
async def test_update_template_content_text_only(db_manager: Any) -> None:
    """update_template_content обновляет только текст."""
    async with db_manager.session() as session:
        user = User(tg_id="tpl_cont", username="tpl_cont")
        cat = TemplateCategory(name="CatCont", sort_order=0)
        session.add_all([user, cat])
        await session.flush()
        t = MessageTemplate(
            title="ContT", content="Old", category_id=cat.id, author_id=user.id
        )
        session.add(t)
        await session.commit()
        tid = t.id

    repo = MessageTemplateRepository(db_manager)
    ok = await repo.update_template_content(tid, {"text": "New content"})
    assert ok is True
    found = await repo.get_template_by_id(tid)
    assert found is not None
    assert found.content == "New content"


@pytest.mark.asyncio
async def test_update_template_content_not_found(db_manager: Any) -> None:
    """update_template_content для несуществующего id возвращает False."""
    repo = MessageTemplateRepository(db_manager)
    assert await repo.update_template_content(99999, {"text": "x"}) is False
