from typing import Any

import pytest
from sqlalchemy.exc import IntegrityError

from models import MessageTemplate, User
from repositories.media_repository import TemplateMediaRepository


@pytest.mark.asyncio
async def test_create_media(db_manager: Any) -> None:
    """Тестирует успешное создание медиа для шаблона."""
    # Arrange
    repo = TemplateMediaRepository(db_manager)
    async with db_manager.session() as session:
        # Создаем автора
        author = User(tg_id="author_1", username="author1")
        session.add(author)
        await session.commit()

        # Создаем шаблон
        template = MessageTemplate(
            title="Test Template", content="Hello!", author_id=author.id
        )
        session.add(template)
        await session.commit()
        template_id = template.id

    # Act
    media = await repo.create_media(
        template_id=template_id,
        media_type="photo",
        file_id="file_id_123",
        file_unique_id="unique_123",
        position=1,
    )

    # Assert
    assert media.id is not None
    assert media.template_id == template_id
    assert media.media_type == "photo"
    assert media.file_id == "file_id_123"
    assert media.file_unique_id == "unique_123"
    assert media.position == 1


@pytest.mark.asyncio
async def test_create_media_invalid_template(db_manager: Any) -> None:
    """Тестирует ошибку при создании медиа для несуществующего шаблона."""
    # Arrange
    repo = TemplateMediaRepository(db_manager)

    # Act & Assert
    with pytest.raises(IntegrityError):
        await repo.create_media(
            template_id=99999,  # Несуществующий ID
            media_type="photo",
            file_id="file_id_err",
            file_unique_id="unique_err",
            position=0,
        )
