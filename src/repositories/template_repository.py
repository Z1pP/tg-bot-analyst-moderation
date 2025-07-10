import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from database.session import async_session
from models import MessageTemplate

logger = logging.getLogger(__name__)


class MessageTemplateRepository:
    async def create_template(
        self,
        title: str,
        content: str,
        category_id: int,
        author_id: int,
    ) -> MessageTemplate:
        async with async_session() as session:
            try:
                new_response = MessageTemplate(
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

    async def get_all_templates(self) -> List[MessageTemplate]:
        async with async_session() as session:
            try:
                query = select(MessageTemplate).options(
                    selectinload(MessageTemplate.media_items),
                    selectinload(MessageTemplate.category),
                )
                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                logger.error("Ошибка при получении всех быстрых ответов: %s", e)
                raise

    async def get_template_by_id(
        self,
        template_id: int,
    ) -> Optional[MessageTemplate]:
        """Получаем быстрый ответ вместе с его медиа"""
        async with async_session() as session:
            try:
                query = (
                    select(MessageTemplate)
                    .options(selectinload(MessageTemplate.media_items))
                    .where(MessageTemplate.id == template_id)
                )
                result = await session.execute(query)
                return result.scalar_one_or_none()
            except Exception as e:
                logger.error("Ошибка при получении быстрого ответа по id: %s", e)
                raise

    async def get_templates_by_category(
        self, category_id: int
    ) -> List[MessageTemplate]:
        async with async_session() as session:
            try:
                query = select(MessageTemplate).where(
                    MessageTemplate.category_id == category_id
                )

                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                logger.error("Ошибка при получении всех быстрых ответов: %s", e)
                raise

    async def increase_usage_count(self, template_id: int) -> None:
        async with async_session() as session:
            try:
                template = await self.get_template_by_id(template_id)

                if template:
                    template.usage_count += 1
                    await session.commit()
                    await session.refresh(template, ["usage_count"])
                    logger.info("Шаблон был использован %d раз", template.usage_count)
                else:
                    logger.info("Шаблон не найден")
            except Exception as e:
                logger.error("Ошибка при обнолени шаблона: %s", e)
                raise

    async def delete_template(self, template_id: int) -> None:
        async with async_session() as session:
            try:
                template = await self.get_template_by_id(template_id)

                if template:
                    await session.delete(template)
                    await session.commit()
                    logger.info("Шаблон успешно удален")
                else:
                    logger.info("Шаблон не найден")
            except Exception as e:
                logger.error("Ошибка при удалении шаблона: %s", e)
                raise
