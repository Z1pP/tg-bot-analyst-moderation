"""Характеризующие тесты TemplateService.

Фиксируют текущее поведение: кеширование страниц категории, счётчики,
пагинацию глобальных/чатовых шаблонов, удаление и переименование.
"""

from unittest.mock import AsyncMock, MagicMock, call

import pytest

from models import MessageTemplate
from repositories import MessageTemplateRepository
from services.caching import ICache
from services.templates.cache_helpers import CATEGORY_CACHE_PAGES
from services.templates.template_service import TemplateService


@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock(spec=MessageTemplateRepository)


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock(spec=ICache)


@pytest.fixture
def service(mock_repo: AsyncMock, mock_cache: AsyncMock) -> TemplateService:
    return TemplateService(template_repository=mock_repo, cache=mock_cache)


@pytest.fixture
def sample_template() -> MagicMock:
    template = MagicMock(spec=MessageTemplate)
    template.id = 10
    template.title = "Template"
    template.category_id = 3
    return template


def _expected_category_keys(category_id: int) -> list:
    return [
        call(f"tpl:cat:{category_id}:page:{page}")
        for page in range(1, CATEGORY_CACHE_PAGES + 1)
    ]


# ---------------------------------------------------------------------------
# get_by_category
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_by_category_returns_cached_value(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """При попадании в кеш репозиторий не вызывается."""
    # Arrange
    cached = [MagicMock(spec=MessageTemplate)]
    mock_cache.get.return_value = cached

    # Act
    result = await service.get_by_category(category_id=3, page=2)

    # Assert
    assert result is cached
    mock_cache.get.assert_awaited_once_with("tpl:cat:3:page:2")
    mock_repo.get_templates_paginated.assert_not_awaited()
    mock_cache.set.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_by_category_cached_empty_list_is_returned(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """Пустой список в кеше не считается промахом (проверка cached is not None)."""
    # Arrange
    mock_cache.get.return_value = []

    # Act
    result = await service.get_by_category(category_id=3)

    # Assert
    assert result == []
    mock_repo.get_templates_paginated.assert_not_awaited()


@pytest.mark.asyncio
async def test_get_by_category_cache_miss_loads_and_caches(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """Промах кеша: читает репозиторий с offset и кеширует на час."""
    # Arrange
    template = MagicMock(spec=MessageTemplate)
    mock_cache.get.return_value = None
    mock_repo.get_templates_paginated.return_value = (template,)

    # Act
    result = await service.get_by_category(category_id=3, page=3, page_size=5)

    # Assert
    assert result == [template]
    mock_cache.get.assert_awaited_once_with("tpl:cat:3:page:3")
    mock_repo.get_templates_paginated.assert_awaited_once_with(
        category_id=3,
        limit=5,
        offset=10,
    )
    mock_cache.set.assert_awaited_once_with(
        "tpl:cat:3:page:3",
        [template],
        ttl=3600,
    )


@pytest.mark.asyncio
async def test_get_by_category_cache_key_ignores_page_size(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """Текущее поведение: размер страницы не входит в ключ кеша."""
    # Arrange
    mock_cache.get.return_value = None
    mock_repo.get_templates_paginated.return_value = []

    # Act
    await service.get_by_category(category_id=3, page=1, page_size=10)

    # Assert
    mock_cache.get.assert_awaited_once_with("tpl:cat:3:page:1")
    mock_cache.set.assert_awaited_once_with("tpl:cat:3:page:1", [], ttl=3600)


@pytest.mark.asyncio
async def test_get_by_category_first_page_uses_zero_offset(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """Для первой страницы offset равен нулю, а размер страницы по умолчанию 5."""
    # Arrange
    mock_cache.get.return_value = None
    mock_repo.get_templates_paginated.return_value = []

    # Act
    result = await service.get_by_category(category_id=7)

    # Assert
    assert result == []
    mock_repo.get_templates_paginated.assert_awaited_once_with(
        category_id=7,
        limit=5,
        offset=0,
    )
    mock_cache.set.assert_awaited_once_with("tpl:cat:7:page:1", [], ttl=3600)


# ---------------------------------------------------------------------------
# Счётчики и пагинация
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_count_calls_repository_without_filters(
    service: TemplateService,
    mock_repo: AsyncMock,
) -> None:
    """get_count запрашивает общий счётчик без аргументов."""
    # Arrange
    mock_repo.get_templates_count.return_value = 42

    # Act
    result = await service.get_count()

    # Assert
    assert result == 42
    mock_repo.get_templates_count.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_get_count_by_category_passes_category_id(
    service: TemplateService,
    mock_repo: AsyncMock,
) -> None:
    """get_count_by_category передаёт category_id в репозиторий."""
    # Arrange
    mock_repo.get_templates_count.return_value = 5

    # Act
    result = await service.get_count_by_category(category_id=3)

    # Assert
    assert result == 5
    mock_repo.get_templates_count.assert_awaited_once_with(category_id=3)


@pytest.mark.asyncio
async def test_get_global_templates_paginated_uses_global_only(
    service: TemplateService,
    mock_repo: AsyncMock,
) -> None:
    """Глобальные шаблоны запрашиваются с global_only=True и offset."""
    # Arrange
    templates = [MagicMock(spec=MessageTemplate)]
    mock_repo.get_templates_paginated.return_value = templates

    # Act
    result = await service.get_global_templates_paginated(page=2, page_size=10)

    # Assert
    assert result is templates
    mock_repo.get_templates_paginated.assert_awaited_once_with(
        offset=10,
        limit=10,
        global_only=True,
    )


@pytest.mark.asyncio
async def test_get_global_templates_count_uses_global_only(
    service: TemplateService,
    mock_repo: AsyncMock,
) -> None:
    """Счётчик глобальных шаблонов запрашивается с global_only=True."""
    # Arrange
    mock_repo.get_templates_count.return_value = 8

    # Act
    result = await service.get_global_templates_count()

    # Assert
    assert result == 8
    mock_repo.get_templates_count.assert_awaited_once_with(global_only=True)


@pytest.mark.asyncio
async def test_get_chat_templates_paginated_passes_chat_id_and_offset(
    service: TemplateService,
    mock_repo: AsyncMock,
) -> None:
    """Шаблоны чата запрашиваются с chat_id, offset и limit."""
    # Arrange
    templates = [MagicMock(spec=MessageTemplate)]
    mock_repo.get_templates_paginated.return_value = templates

    # Act
    result = await service.get_chat_templates_paginated(chat_id=1, page=3)

    # Assert
    assert result is templates
    mock_repo.get_templates_paginated.assert_awaited_once_with(
        chat_id=1,
        offset=10,
        limit=5,
    )


@pytest.mark.asyncio
async def test_get_chat_templates_count_passes_chat_id(
    service: TemplateService,
    mock_repo: AsyncMock,
) -> None:
    """Счётчик шаблонов чата запрашивается с chat_id."""
    # Arrange
    mock_repo.get_templates_count.return_value = 2

    # Act
    result = await service.get_chat_templates_count(chat_id=1)

    # Assert
    assert result == 2
    mock_repo.get_templates_count.assert_awaited_once_with(chat_id=1)


# ---------------------------------------------------------------------------
# Получение шаблонов
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_template_by_id_returns_template(
    service: TemplateService,
    mock_repo: AsyncMock,
    sample_template: MagicMock,
) -> None:
    """get_template_by_id делегирует в репозиторий."""
    # Arrange
    mock_repo.get_template_by_id.return_value = sample_template

    # Act
    result = await service.get_template_by_id(template_id=10)

    # Assert
    assert result is sample_template
    mock_repo.get_template_by_id.assert_awaited_once_with(10)


@pytest.mark.asyncio
async def test_get_template_by_id_returns_none_when_missing(
    service: TemplateService,
    mock_repo: AsyncMock,
) -> None:
    """get_template_by_id возвращает None, если шаблона нет."""
    # Arrange
    mock_repo.get_template_by_id.return_value = None

    # Act
    result = await service.get_template_by_id(template_id=999)

    # Assert
    assert result is None


@pytest.mark.asyncio
async def test_get_template_and_increase_usage_passes_arguments(
    service: TemplateService,
    mock_repo: AsyncMock,
    sample_template: MagicMock,
) -> None:
    """get_template_and_increase_usage делегирует id и chat_id."""
    # Arrange
    mock_repo.get_template_and_increase_usage_count.return_value = sample_template

    # Act
    result = await service.get_template_and_increase_usage(
        template_id=10,
        chat_id="1",
    )

    # Assert
    assert result is sample_template
    mock_repo.get_template_and_increase_usage_count.assert_awaited_once_with(
        template_id=10,
        chat_id="1",
    )


@pytest.mark.asyncio
async def test_get_templates_by_query_passes_query(
    service: TemplateService,
    mock_repo: AsyncMock,
) -> None:
    """get_templates_by_query делегирует поисковый запрос."""
    # Arrange
    templates = [MagicMock(spec=MessageTemplate)]
    mock_repo.get_templates_by_query.return_value = templates

    # Act
    result = await service.get_templates_by_query(query="hello")

    # Assert
    assert result is templates
    mock_repo.get_templates_by_query.assert_awaited_once_with(query="hello")


# ---------------------------------------------------------------------------
# delete_template
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_template_returns_false_when_not_found(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """Отсутствующий шаблон: False без удаления и инвалидации кеша."""
    # Arrange
    mock_repo.get_template_by_id.return_value = None

    # Act
    result = await service.delete_template(template_id=999)

    # Assert
    assert result is False
    mock_repo.delete_template.assert_not_awaited()
    mock_cache.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_template_invalidates_category_pages(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_template: MagicMock,
) -> None:
    """Успешное удаление шаблона с категорией чистит страницы категории."""
    # Arrange
    mock_repo.get_template_by_id.return_value = sample_template
    mock_repo.delete_template.return_value = True

    # Act
    result = await service.delete_template(template_id=10)

    # Assert
    assert result is True
    mock_repo.delete_template.assert_awaited_once_with(10)
    assert mock_cache.delete.await_args_list == _expected_category_keys(3)


@pytest.mark.asyncio
async def test_delete_template_without_category_does_not_invalidate(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_template: MagicMock,
) -> None:
    """Шаблон без категории удаляется без инвалидации кеша."""
    # Arrange
    sample_template.category_id = None
    mock_repo.get_template_by_id.return_value = sample_template
    mock_repo.delete_template.return_value = True

    # Act
    result = await service.delete_template(template_id=10)

    # Assert
    assert result is True
    mock_cache.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_delete_template_does_not_invalidate_when_repo_returns_false(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_template: MagicMock,
) -> None:
    """Если репозиторий не удалил шаблон, кеш не трогается."""
    # Arrange
    mock_repo.get_template_by_id.return_value = sample_template
    mock_repo.delete_template.return_value = False

    # Act
    result = await service.delete_template(template_id=10)

    # Assert
    assert result is False
    mock_cache.delete.assert_not_awaited()


# ---------------------------------------------------------------------------
# update_template_title
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_template_title_success_invalidates_cache(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_template: MagicMock,
) -> None:
    """Успешное переименование инвалидирует страницы категории шаблона."""
    # Arrange
    mock_repo.update_template_title.return_value = True
    mock_repo.get_template_by_id.return_value = sample_template

    # Act
    result = await service.update_template_title(template_id=10, new_title="New")

    # Assert
    assert result is True
    mock_repo.update_template_title.assert_awaited_once_with(10, "New")
    assert mock_cache.delete.await_args_list == _expected_category_keys(3)


@pytest.mark.asyncio
async def test_update_template_title_without_category_does_not_invalidate(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_template: MagicMock,
) -> None:
    """Шаблон без категории переименовывается без инвалидации."""
    # Arrange
    sample_template.category_id = None
    mock_repo.update_template_title.return_value = True
    mock_repo.get_template_by_id.return_value = sample_template

    # Act
    result = await service.update_template_title(template_id=10, new_title="New")

    # Assert
    assert result is True
    mock_cache.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_template_title_returns_false_and_skips_lookup(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """Неуспешное переименование не перечитывает шаблон и не чистит кеш."""
    # Arrange
    mock_repo.update_template_title.return_value = False

    # Act
    result = await service.update_template_title(template_id=10, new_title="New")

    # Assert
    assert result is False
    mock_repo.get_template_by_id.assert_not_awaited()
    mock_cache.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_template_title_missing_template_after_update(
    service: TemplateService,
    mock_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """Если после обновления шаблон не найден, кеш не инвалидируется."""
    # Arrange
    mock_repo.update_template_title.return_value = True
    mock_repo.get_template_by_id.return_value = None

    # Act
    result = await service.update_template_title(template_id=10, new_title="New")

    # Assert
    assert result is True
    mock_cache.delete.assert_not_awaited()


# ---------------------------------------------------------------------------
# invalidate_category_cache
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalidate_category_cache_deletes_all_pages(
    service: TemplateService,
    mock_cache: AsyncMock,
) -> None:
    """invalidate_category_cache удаляет 10 страниц указанной категории."""
    # Act
    result = await service.invalidate_category_cache(category_id=5)

    # Assert
    assert result is None
    assert mock_cache.delete.await_args_list == _expected_category_keys(5)