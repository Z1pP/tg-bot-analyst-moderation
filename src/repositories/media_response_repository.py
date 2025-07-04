import logging
from typing import Optional

from database.session import async_session
from models import QuickResponseMedia

logger = logging.getLogger(__name__)


class QuickResponseMediaRepository:
    async def create_media(
        self,
        response_id: int,
        media_type: str,
        file_id: str,
        file_unique_id: str,
        position: int,
    ) -> Optional[QuickResponseMedia]:
        async with async_session() as session:
            try:
                new_media = QuickResponseMedia(
                    response_id=response_id,
                    media_type=media_type,
                    file_id=file_id,
                    file_unique_id=file_unique_id,
                    position=position,
                )

                session.add(new_media)
                await session.commit()
                await session.refresh(new_media)

                logger.info(
                    "Успешно создана новая медиа для быстрого ответа с id=%d",
                    new_media.id,
                )

                return new_media
            except Exception as e:
                logger.error(
                    "Ошибка при создании новой медиа для быстрого ответа: %s", e
                )
                raise
