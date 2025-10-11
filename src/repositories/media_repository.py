import logging
from typing import Optional

from database.session import DatabaseContextManager
from models import TemplateMedia

logger = logging.getLogger(__name__)


class TemplateMediaRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

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
            except Exception as e:
                logger.error("Ошибка при создании новой медиа для шаблона: %s", e)
                raise
