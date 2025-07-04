import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.session import async_session
from models import QuickResponse

logger = logging.getLogger(__name__)


class QuickResponseRepository:
    async def create_quick_response(
        self,
        title: str,
        content: str,
        category_id: int,
        author_id: int,
    ) -> QuickResponse:
        async with async_session() as session:
            try:
                new_response = QuickResponse(
                    title=title,
                    content=content,
                    category_id=category_id,
                    author_id=author_id,
                )

                session.add(new_response)
                await session.commit()
                await session.refresh(new_response)

                logger.info(
                    "Успешно создан новый быстрый ответ с id=%d", new_response.id
                )

                return new_response
            except Exception as e:
                logger.error("Ошибка при создании нового быстрого ответа: %s", e)
                raise

    async def get_all_quick_responses(self) -> List[QuickResponse]:
        async with async_session() as session:
            try:
                query = select(QuickResponse).options(
                    selectinload(QuickResponse.media_items),
                    selectinload(QuickResponse.category),
                )
                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                logger.error("Ошибка при получении всех быстрых ответов: %s", e)
                raise

    async def get_quick_response_by_id(
        self,
        response_id: int,
    ) -> Optional[QuickResponse]:
        """Получаем быстрый ответ вместе с его медиа"""
        async with async_session() as session:
            try:
                query = (
                    select(QuickResponse)
                    .options(selectinload(QuickResponse.media_items))
                    .where(QuickResponse.id == response_id)
                )
                result = await session.execute(query)
                return result.scalar_one_or_none()
            except Exception as e:
                logger.error("Ошибка при получении быстрого ответа по id: %s", e)
                raise
