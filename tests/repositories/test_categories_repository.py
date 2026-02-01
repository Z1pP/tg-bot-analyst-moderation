from typing import Any

import pytest

from repositories.categories_repository import TemplateCategoryRepository


@pytest.mark.asyncio
async def test_create_category(db_manager: Any) -> None:
    """Тестирует создание категории и инкремент sort_order."""
    # Arrange
    repo = TemplateCategoryRepository(db_manager)

    # Act - первая категория
    cat1 = await repo.create_category(name="Category 1")
    # Act - вторая категория
    cat2 = await repo.create_category(name="Category 2")

    # Assert
    assert cat1.id is not None
    assert cat1.name == "Category 1"
    assert cat1.sort_order == 1

    assert cat2.id is not None
    assert cat2.name == "Category 2"
    assert cat2.sort_order == 2


@pytest.mark.asyncio
async def test_get_all_categories(db_manager: Any) -> None:
    """Тестирует получение всех категорий и их сортировку."""
    # Arrange
    repo = TemplateCategoryRepository(db_manager)
    c1 = await repo.create_category(name="Cat B")
    c2 = await repo.create_category(name="Cat A")
    c3 = await repo.create_category(name="Cat C")

    # Act
    categories = await repo.get_all_categories()

    # Assert
    # Фильтруем только те, что создали в этом тесте
    test_cats = [c for c in categories if c.name in ["Cat B", "Cat A", "Cat C"]]
    assert len(test_cats) == 3
    # Проверяем, что категории отсортированы по sort_order (в порядке создания)
    assert test_cats[0].name == "Cat B"
    assert test_cats[1].name == "Cat A"
    assert test_cats[2].name == "Cat C"


@pytest.mark.asyncio
async def test_get_category_by_id(db_manager: Any) -> None:
    """Тестирует получение категории по ID."""
    # Arrange
    repo = TemplateCategoryRepository(db_manager)
    created = await repo.create_category(name="ByID")

    # Act
    found = await repo.get_category_by_id(created.id)

    # Assert
    assert found is not None
    assert found.id == created.id
    assert found.name == "ByID"


@pytest.mark.asyncio
async def test_get_last_category(db_manager: Any) -> None:
    """Тестирует получение последней категории (с макс sort_order)."""
    # Arrange
    repo = TemplateCategoryRepository(db_manager)
    await repo.create_category(name="First")
    last = await repo.create_category(name="Last")

    # Act
    found_last = await repo.get_last_category()

    # Assert
    assert found_last is not None
    assert found_last.name == "Last"
    assert found_last.id == last.id


@pytest.mark.asyncio
async def test_update_category_name(db_manager: Any) -> None:
    """Тестирует обновление названия категории."""
    # Arrange
    repo = TemplateCategoryRepository(db_manager)
    category = await repo.create_category(name="Old Name")

    # Act
    updated = await repo.update_category_name(category.id, "New Name")

    # Assert
    assert updated.name == "New Name"

    # Verify in DB
    refreshed = await repo.get_category_by_id(category.id)
    assert refreshed.name == "New Name"


@pytest.mark.asyncio
async def test_delete_category(db_manager: Any) -> None:
    """Тестирует удаление категории."""
    # Arrange
    repo = TemplateCategoryRepository(db_manager)
    category = await repo.create_category(name="Delete Me")
    cat_id = category.id

    # Act
    await repo.delete_category(cat_id)

    # Assert
    found = await repo.get_category_by_id(cat_id)
    assert found is None


@pytest.mark.asyncio
async def test_pagination(db_manager: Any) -> None:
    """Тестирует пагинацию и подсчет общего количества категорий."""
    # Arrange
    repo = TemplateCategoryRepository(db_manager)
    # Создаем 7 категорий
    for i in range(7):
        await repo.create_category(name=f"Cat {i}")

    # Act
    total_count = await repo.get_categories_count()
    # Получаем все категории, чтобы знать смещение
    all_cats = await repo.get_all_categories()

    # Первая страница (limit 5)
    page1 = await repo.get_categories_paginated(limit=5, offset=0)
    # Вторая страница (limit 5)
    page2 = await repo.get_categories_paginated(limit=5, offset=5)

    # Assert
    assert total_count >= 7
    assert len(page1) == 5
    if total_count == 7:
        assert len(page2) == 2
    else:
        assert len(page2) >= 2
