import logging
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from models import TemplateMedia
from repositories.base import BaseRepository, transactional

logger = logging.getLogger(__name__)


class TemplateMediaRepository(BaseRepository):
    @transactional
    async def create_media(
        self,
        session: AsyncSession,
        /,
        template_id: int,
        media_type: str,
        file_id: str,
        file_unique_id: str,
        position: int,
    ) -> Optional[TemplateMedia]:
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
