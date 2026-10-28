"""Характеризующие тесты TemplateContentService.

Фиксируют текущее поведение: извлечение медиа из сообщений, сохранение
шаблона и медиа, обновление контента и инвалидацию кеша.
"""

from unittest.mock import AsyncMock, MagicMock, call

import pytest
from sqlalchemy.exc import SQLAlchemyError

from constants.enums import AdminActionType
from models import MessageTemplate, User
from repositories import (
    MessageTemplateRepository,
    TemplateMediaRepository,
    UserRepository,
)
from services.admin_action_log_service import AdminActionLogService
from services.caching import ICache
from services.templates.cache_helpers import CATEGORY_CACHE_PAGES
from services.templates.content_service import TemplateContentService


def _make_message(
    *,
    text: str = None,
    caption: str = None,
    photo: list = None,
    document: object = None,
    video: object = None,
    animation: object = None,
) -> MagicMock:
    """Создаёт мок сообщения с заданными атрибутами."""
    message = MagicMock()
    message.html_text = text
    message.caption = caption
    message.photo = photo
    message.document = document
    message.video = video
    message.animation = animation
    return message


def _make_media(file_id: str, unique_id: str) -> MagicMock:
    """Мок файла Telegram с file_id и file_unique_id."""
    media = MagicMock()
    media.file_id = file_id
    media.file_unique_id = unique_id
    return media


def _expected_category_keys(category_id: int) -> list:
    return [
        call(f"tpl:cat:{category_id}:page:{page}")
        for page in range(1, CATEGORY_CACHE_PAGES + 1)
    ]


@pytest.fixture
def mock_user_repo() -> AsyncMock:
    return AsyncMock(spec=UserRepository)


@pytest.fixture
def mock_template_repo() -> AsyncMock:
    return AsyncMock(spec=MessageTemplateRepository)


@pytest.fixture
def mock_media_repo() -> AsyncMock:
    return AsyncMock(spec=TemplateMediaRepository)


@pytest.fixture
def mock_cache() -> AsyncMock:
    return AsyncMock(spec=ICache)


@pytest.fixture
def service(
    mock_user_repo: AsyncMock,
    mock_template_repo: AsyncMock,
    mock_media_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> TemplateContentService:
    return TemplateContentService(
        user_repository=mock_user_repo,
        template_repository=mock_template_repo,
        media_repository=mock_media_repo,
        cache=mock_cache,
    )


@pytest.fixture
def sample_user() -> MagicMock:
    user = MagicMock(spec=User)
    user.id = 1
    user.tg_id = "100"
    return user


@pytest.fixture
def sample_template() -> MagicMock:
    template = MagicMock(spec=MessageTemplate)
    template.id = 10
    template.category_id = 3
    return template


# ---------------------------------------------------------------------------
# extract_media_content
# ---------------------------------------------------------------------------


def test_extract_photo_uses_largest_size(service: TemplateContentService) -> None:
    """Для фото берётся последний (наибольший) размер и его file_id."""
    # Arrange
    smallest = _make_media("small", "uniq_small")
    largest = _make_media("large", "uniq_large")
    message = _make_message(text="<b>hi</b>", photo=[smallest, largest])

    # Act
    result = service.extract_media_content([message])

    # Assert
    assert result == {
        "text": "<b>hi</b>",
        "media_types": ["photo"],
        "media_files": ["large"],
        "media_unique_ids": ["uniq_large"],
    }


def test_extract_document(service: TemplateContentService) -> None:
    """Документ извлекается из message.document."""
    # Arrange
    message = _make_message(
        text="doc text",
        document=_make_media("doc_file", "doc_uniq"),
    )

    # Act
    result = service.extract_media_content([message])

    # Assert
    assert result["media_types"] == ["document"]
    assert result["media_files"] == ["doc_file"]
    assert result["media_unique_ids"] == ["doc_uniq"]
    assert result["text"] == "doc text"


def test_extract_video(service: TemplateContentService) -> None:
    """Видео извлекается из message.video."""
    # Arrange
    message = _make_message(
        text="video text",
        video=_make_media("video_file", "video_uniq"),
    )

    # Act
    result = service.extract_media_content([message])

    # Assert
    assert result["media_types"] == ["video"]
    assert result["media_files"] == ["video_file"]
    assert result["media_unique_ids"] == ["video_uniq"]


def test_extract_animation(service: TemplateContentService) -> None:
    """Анимация извлекается из message.animation."""
    # Arrange
    message = _make_message(
        text="gif text",
        animation=_make_media("gif_file", "gif_uniq"),
    )

    # Act
    result = service.extract_media_content([message])

    # Assert
    assert result["media_types"] == ["animation"]
    assert result["media_files"] == ["gif_file"]
    assert result["media_unique_ids"] == ["gif_uniq"]


def test_extract_album_collects_media_from_all_messages(
    service: TemplateContentService,
) -> None:
    """Текст берётся из первого сообщения, медиа собираются со всех."""
    # Arrange
    first = _make_message(
        text="album",
        photo=[_make_media("p1", "pu1")],
    )
    second = _make_message(
        text=None,
        document=_make_media("d1", "du1"),
    )

    # Act
    result = service.extract_media_content([first, second])

    # Assert
    assert result["text"] == "album"
    assert result["media_types"] == ["photo", "document"]
    assert result["media_files"] == ["p1", "d1"]
    assert result["media_unique_ids"] == ["pu1", "du1"]


def test_extract_uses_caption_when_html_text_missing(
    service: TemplateContentService,
) -> None:
    """Если html_text пуст, используется caption первого сообщения."""
    # Arrange
    message = _make_message(text=None, caption="caption text")

    # Act
    result = service.extract_media_content([message])

    # Assert
    assert result["text"] == "caption text"
    assert result["media_types"] == []
    assert result["media_files"] == []
    assert result["media_unique_ids"] == []


def test_extract_returns_empty_text_when_no_text_and_no_caption(
    service: TemplateContentService,
) -> None:
    """Без текста и подписи поле text остаётся пустой строкой."""
    # Arrange
    message = _make_message(text=None, caption=None)

    # Act
    result = service.extract_media_content([message])

    # Assert
    assert result["text"] == ""


def test_extract_prefers_photo_when_multiple_media_types_present(
    service: TemplateContentService,
) -> None:
    """При нескольких типах в одном сообщении побеждает первый по порядку (photo)."""
    # Arrange
    message = _make_message(
        text="both",
        photo=[_make_media("p1", "pu1")],
        document=_make_media("d1", "du1"),
    )

    # Act
    result = service.extract_media_content([message])

    # Assert
    assert result["media_types"] == ["photo"]
    assert result["media_files"] == ["p1"]


def test_extract_empty_messages_returns_empty_content(
    service: TemplateContentService,
) -> None:
    """Пустой список сообщений даёт пустой контент без исключения."""
    # Act
    content = service.extract_media_content([])

    # Assert
    assert content["text"] == ""
    assert content["media_types"] == []
    assert content["media_files"] == []
    assert content["media_unique_ids"] == []


# ---------------------------------------------------------------------------
# save_template
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_template_raises_when_user_not_found(
    service: TemplateContentService,
    mock_user_repo: AsyncMock,
    mock_template_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """Если автор не найден, save_template поднимает ValueError."""
    # Arrange
    mock_user_repo.get_user_by_username.return_value = None

    # Act / Assert
    with pytest.raises(ValueError, match="User not found"):
        await service.save_template(
            author_username="ghost",
            content={"title": "T", "text": "C"},
        )
    mock_template_repo.create_template.assert_not_awaited()
    mock_cache.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_template_uses_defaults_and_returns_template(
    service: TemplateContentService,
    mock_user_repo: AsyncMock,
    mock_template_repo: AsyncMock,
    sample_user: MagicMock,
    sample_template: MagicMock,
) -> None:
    """Пустой контент сохраняется с названием по умолчанию и пустым текстом."""
    # Arrange
    mock_user_repo.get_user_by_username.return_value = sample_user
    mock_template_repo.create_template.return_value = sample_template
    service.save_media_files = AsyncMock()

    # Act
    result = await service.save_template(author_username="author", content={})

    # Assert
    assert result is sample_template
    mock_user_repo.get_user_by_username.assert_awaited_once_with(
        username="author"
    )
    mock_template_repo.create_template.assert_awaited_once_with(
        title="Без названия",
        content="",
        category_id=None,
        author_id=1,
        chat_id=None,
    )
    service.save_media_files.assert_awaited_once_with(
        template_id=10,
        content={},
    )


@pytest.mark.asyncio
async def test_save_template_passes_content_fields(
    service: TemplateContentService,
    mock_user_repo: AsyncMock,
    mock_template_repo: AsyncMock,
    sample_user: MagicMock,
    sample_template: MagicMock,
) -> None:
    """Поля content попадают в create_template, медиа сохраняются с id шаблона."""
    # Arrange
    mock_user_repo.get_user_by_username.return_value = sample_user
    mock_template_repo.create_template.return_value = sample_template
    service.save_media_files = AsyncMock()
    content = {
        "title": "Title",
        "text": "Text",
        "category_id": 3,
        "chat_id": 7,
    }

    # Act
    await service.save_template(author_username="author", content=content)

    # Assert
    mock_template_repo.create_template.assert_awaited_once_with(
        title="Title",
        content="Text",
        category_id=3,
        author_id=1,
        chat_id=7,
    )
    service.save_media_files.assert_awaited_once_with(
        template_id=10,
        content=content,
    )


@pytest.mark.asyncio
async def test_save_template_invalidates_category_cache(
    service: TemplateContentService,
    mock_user_repo: AsyncMock,
    mock_template_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_user: MagicMock,
    sample_template: MagicMock,
) -> None:
    """При наличии category_id инвалидируются 10 страниц категории."""
    # Arrange
    mock_user_repo.get_user_by_username.return_value = sample_user
    mock_template_repo.create_template.return_value = sample_template
    service.save_media_files = AsyncMock()

    # Act
    await service.save_template(
        author_username="author",
        content={"category_id": 3},
    )

    # Assert
    assert mock_cache.delete.await_args_list == _expected_category_keys(3)


@pytest.mark.asyncio
async def test_save_template_logs_admin_action(
    mock_user_repo: AsyncMock,
    mock_template_repo: AsyncMock,
    mock_media_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_user: MagicMock,
    sample_template: MagicMock,
) -> None:
    """При наличии log-сервиса и tg_id пишется ADD_TEMPLATE."""
    # Arrange
    mock_admin_log = AsyncMock(spec=AdminActionLogService)
    service = TemplateContentService(
        user_repository=mock_user_repo,
        template_repository=mock_template_repo,
        media_repository=mock_media_repo,
        cache=mock_cache,
        admin_action_log_service=mock_admin_log,
    )
    service.save_media_files = AsyncMock()
    mock_user_repo.get_user_by_username.return_value = sample_user
    mock_template_repo.create_template.return_value = sample_template

    # Act
    await service.save_template(author_username="author", content={})

    # Assert
    mock_admin_log.log_action.assert_awaited_once_with(
        admin_tg_id="100",
        action_type=AdminActionType.ADD_TEMPLATE,
    )


@pytest.mark.asyncio
async def test_save_template_skips_log_without_user_tg_id(
    mock_user_repo: AsyncMock,
    mock_template_repo: AsyncMock,
    mock_media_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_user: MagicMock,
    sample_template: MagicMock,
) -> None:
    """Если у пользователя нет tg_id, действие не логируется."""
    # Arrange
    sample_user.tg_id = None
    mock_admin_log = AsyncMock(spec=AdminActionLogService)
    service = TemplateContentService(
        user_repository=mock_user_repo,
        template_repository=mock_template_repo,
        media_repository=mock_media_repo,
        cache=mock_cache,
        admin_action_log_service=mock_admin_log,
    )
    service.save_media_files = AsyncMock()
    mock_user_repo.get_user_by_username.return_value = sample_user
    mock_template_repo.create_template.return_value = sample_template

    # Act
    await service.save_template(author_username="author", content={})

    # Assert
    mock_admin_log.log_action.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_template_skips_log_without_log_service(
    service: TemplateContentService,
    mock_user_repo: AsyncMock,
    mock_template_repo: AsyncMock,
    sample_user: MagicMock,
    sample_template: MagicMock,
) -> None:
    """Без admin_action_log_service сохранение проходит без логирования."""
    # Arrange
    mock_user_repo.get_user_by_username.return_value = sample_user
    mock_template_repo.create_template.return_value = sample_template
    service.save_media_files = AsyncMock()

    # Act
    result = await service.save_template(author_username="author", content={})

    # Assert
    assert result is sample_template


@pytest.mark.asyncio
async def test_save_template_reraises_sqlalchemy_error(
    service: TemplateContentService,
    mock_user_repo: AsyncMock,
    mock_template_repo: AsyncMock,
    sample_user: MagicMock,
    mock_cache: AsyncMock,
) -> None:
    """SQLAlchemyError при создании шаблона пробрасывается наружу."""
    # Arrange
    mock_user_repo.get_user_by_username.return_value = sample_user
    mock_template_repo.create_template.side_effect = SQLAlchemyError("db down")

    # Act / Assert
    with pytest.raises(SQLAlchemyError):
        await service.save_template(author_username="author", content={})
    mock_cache.delete.assert_not_awaited()


# ---------------------------------------------------------------------------
# save_media_files
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_save_media_files_creates_media_with_positions(
    service: TemplateContentService,
    mock_media_repo: AsyncMock,
) -> None:
    """Медиа создаются по порядку с position 0..n-1."""
    # Arrange
    content = {
        "media_files": ["f1", "f2"],
        "media_unique_ids": ["u1", "u2"],
        "media_types": ["photo", "document"],
    }

    # Act
    result = await service.save_media_files(template_id=10, content=content)

    # Assert
    assert result is None
    assert mock_media_repo.create_media.await_args_list == [
        call(
            template_id=10,
            media_type="photo",
            file_id="f1",
            file_unique_id="u1",
            position=0,
        ),
        call(
            template_id=10,
            media_type="document",
            file_id="f2",
            file_unique_id="u2",
            position=1,
        ),
    ]


@pytest.mark.asyncio
async def test_save_media_files_skips_when_no_files(
    service: TemplateContentService,
    mock_media_repo: AsyncMock,
) -> None:
    """Без media_files сохранение не выполняется."""
    # Act
    await service.save_media_files(template_id=10, content={"media_types": ["photo"]})

    # Assert
    mock_media_repo.create_media.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_media_files_skips_when_no_types(
    service: TemplateContentService,
    mock_media_repo: AsyncMock,
) -> None:
    """Без media_types сохранение не выполняется даже при наличии файлов."""
    # Act
    await service.save_media_files(
        template_id=10,
        content={
            "media_files": ["f1"],
            "media_unique_ids": ["u1"],
        },
    )

    # Assert
    mock_media_repo.create_media.assert_not_awaited()


@pytest.mark.asyncio
async def test_save_media_files_zip_truncates_mismatched_lists(
    service: TemplateContentService,
    mock_media_repo: AsyncMock,
) -> None:
    """zip обрезает списки по кратчайшему: лишние файлы молча теряются."""
    # Arrange
    content = {
        "media_files": ["f1", "f2"],
        "media_unique_ids": ["u1"],
        "media_types": ["photo", "document"],
    }

    # Act
    await service.save_media_files(template_id=10, content=content)

    # Assert
    mock_media_repo.create_media.assert_awaited_once_with(
        template_id=10,
        media_type="photo",
        file_id="f1",
        file_unique_id="u1",
        position=0,
    )


@pytest.mark.asyncio
async def test_save_media_files_continues_after_sqlalchemy_error(
    service: TemplateContentService,
    mock_media_repo: AsyncMock,
) -> None:
    """Ошибка БД на одном файле логируется, остальные сохраняются."""
    # Arrange
    content = {
        "media_files": ["f1", "f2"],
        "media_unique_ids": ["u1", "u2"],
        "media_types": ["photo", "video"],
    }
    mock_media_repo.create_media.side_effect = [SQLAlchemyError("db down"), None]

    # Act
    result = await service.save_media_files(template_id=10, content=content)

    # Assert
    assert result is None
    assert mock_media_repo.create_media.await_count == 2
    second_call = mock_media_repo.create_media.await_args_list[1]
    assert second_call.kwargs["file_id"] == "f2"


# ---------------------------------------------------------------------------
# update_template_content
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_template_content_builds_media_items_and_invalidates(
    service: TemplateContentService,
    mock_template_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_template: MagicMock,
) -> None:
    """Обновление передаёт text и media_items, затем чистит страницы категории."""
    # Arrange
    mock_template_repo.update_template_content.return_value = True
    mock_template_repo.get_template_by_id.return_value = sample_template
    content = {
        "text": "new text",
        "media_files": ["f1"],
        "media_unique_ids": ["u1"],
        "media_types": ["photo"],
    }

    # Act
    result = await service.update_template_content(template_id=10, content=content)

    # Assert
    assert result is True
    mock_template_repo.update_template_content.assert_awaited_once_with(
        10,
        {
            "text": "new text",
            "media_items": [
                {
                    "file_id": "f1",
                    "file_unique_id": "u1",
                    "media_type": "photo",
                }
            ],
        },
    )
    assert mock_cache.delete.await_args_list == _expected_category_keys(3)


@pytest.mark.asyncio
async def test_update_template_content_empty_media(
    service: TemplateContentService,
    mock_template_repo: AsyncMock,
    sample_template: MagicMock,
) -> None:
    """Без медиа media_items остаётся пустым списком."""
    # Arrange
    mock_template_repo.update_template_content.return_value = True
    mock_template_repo.get_template_by_id.return_value = sample_template

    # Act
    result = await service.update_template_content(
        template_id=10,
        content={"text": "only text"},
    )

    # Assert
    assert result is True
    mock_template_repo.update_template_content.assert_awaited_once_with(
        10,
        {"text": "only text", "media_items": []},
    )


@pytest.mark.asyncio
async def test_update_template_content_skips_cache_when_no_category(
    service: TemplateContentService,
    mock_template_repo: AsyncMock,
    mock_cache: AsyncMock,
    sample_template: MagicMock,
) -> None:
    """Шаблон без категории обновляется без инвалидации кеша."""
    # Arrange
    sample_template.category_id = None
    mock_template_repo.update_template_content.return_value = True
    mock_template_repo.get_template_by_id.return_value = sample_template

    # Act
    result = await service.update_template_content(
        template_id=10,
        content={"text": "text"},
    )

    # Assert
    assert result is True
    mock_cache.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_template_content_missing_template_skips_cache(
    service: TemplateContentService,
    mock_template_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """Если шаблон не найден после обновления, кеш не инвалидируется."""
    # Arrange
    mock_template_repo.update_template_content.return_value = True
    mock_template_repo.get_template_by_id.return_value = None

    # Act
    result = await service.update_template_content(
        template_id=10,
        content={"text": "text"},
    )

    # Assert
    assert result is True
    mock_cache.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_template_content_returns_false_and_skips_lookup(
    service: TemplateContentService,
    mock_template_repo: AsyncMock,
    mock_cache: AsyncMock,
) -> None:
    """Если репозиторий вернул False, шаблон не перечитывается."""
    # Arrange
    mock_template_repo.update_template_content.return_value = False

    # Act
    result = await service.update_template_content(
        template_id=10,
        content={"text": "text"},
    )

    # Assert
    assert result is False
    mock_template_repo.get_template_by_id.assert_not_awaited()
    mock_cache.delete.assert_not_awaited()


@pytest.mark.asyncio
async def test_update_template_content_returns_false_on_sqlalchemy_error(
    service: TemplateContentService,
    mock_template_repo: AsyncMock,
) -> None:
    """SQLAlchemyError при обновлении проглатывается и даёт False."""
    # Arrange
    mock_template_repo.update_template_content.side_effect = SQLAlchemyError("db")

    # Act
    result = await service.update_template_content(
        template_id=10,
        content={"text": "text"},
    )

    # Assert
    assert result is False


@pytest.mark.asyncio
async def test_update_template_content_returns_false_on_type_error(
    service: TemplateContentService,
    mock_template_repo: AsyncMock,
) -> None:
    """TypeError при обновлении проглатывается и даёт False."""
    # Arrange
    mock_template_repo.update_template_content.side_effect = TypeError("bad")

    # Act
    result = await service.update_template_content(
        template_id=10,
        content={"text": "text"},
    )

    # Assert
    assert result is False