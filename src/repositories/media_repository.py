import logging
from typing import Optional

from sqlalchemy.exc import SQLAlchemyError

from exceptions import DatabaseException
from models import TemplateMedia
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class TemplateMediaRepository(BaseRepository):
    async def create_media(
        self,
        template_id: int,
        media_type: str,
        file_id: str,
        file_unique_id: str,
        position: int,
    ) -> Optional[TemplateMedia]:
        async with self._db.session() as session:
            try:
                new_media = TemplateMedia(
                    template_id=template_id,
                    media_type=media_type,
                    file_id=file_id,
                    file_unique_id=file_unique_id,
                    position=position,
                )

                session.add(new_media)
                await session.commit()
                await session.refresh(new_media)

                logger.info(
                    "Успешно создана новая медиа для шаблона с id=%d",
                    new_media.id,
                )

                return new_media
            except SQLAlchemyError as e:
                logger.error("Ошибка при создании новой медиа для шаблона: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "create_media", "original": str(e)}
                ) from e
