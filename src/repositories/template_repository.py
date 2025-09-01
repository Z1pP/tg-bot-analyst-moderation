import logging
from typing import List, Optional

from sqlalchemy import and_, func, select
from sqlalchemy.orm import selectinload

from database.session import async_session
from models import ChatSession, MessageTemplate

logger = logging.getLogger(__name__)


class MessageTemplateRepository:
    async def create_template(
        self,
        title: str,
        content: str,
        category_id: int,
        author_id: int,
        chat_id: Optional[int] = None,
    ) -> MessageTemplate:
        async with async_session() as session:
            try:
                new_template = MessageTemplate(
                    title=title,
                    content=content,
                    category_id=category_id,
                    author_id=author_id,
                    chat_id=chat_id,
                )

                session.add(new_template)
                await session.commit()
                await session.refresh(new_template)

                logger.info(f"Создан шаблон с id={new_template.id}")

                return new_template
            except Exception as e:
                logger.error(f"Ошибка при создании шаблона: {e}")
                await session.rollback()
                raise

    async def get_templates_by_query(self, query: str) -> List[MessageTemplate]:
        async with async_session() as session:
            try:
                # Подзапрос для получения минимальных ID уникальных заголовков
                subquery = (
                    select(
                        MessageTemplate.title,
                        func.min(MessageTemplate.id).label("min_id"),
                    )
                    .where(MessageTemplate.title.ilike(f"%{query}%"))
                    .group_by(MessageTemplate.title)
                    .subquery()
                )

                # Основной запрос - выбираем только записи с минимальными ID
                query_obj = (
                    select(MessageTemplate)
                    .join(
                        subquery,
                        and_(
                            MessageTemplate.title == subquery.c.title,
                            MessageTemplate.id == subquery.c.min_id,
                        ),
                    )
                    .options(
                        selectinload(MessageTemplate.media_items),
                        selectinload(MessageTemplate.category),
                    )
                    .order_by(MessageTemplate.usage_count.desc())
                )

                result = await session.execute(query_obj)
                return result.scalars().all()

            except Exception as e:
                logger.error(f"Ошибка при поиске шаблонов: {e}")
                raise

    async def get_templates_count_by_category(self, category_id: int) -> int:
        async with async_session() as session:
            try:
                query = select(func.count(MessageTemplate.id)).where(
                    MessageTemplate.category_id == category_id
                )
                result = await session.execute(query)
                return result.scalar_one()
            except Exception as e:
                logger.error("Ошибка при получении количества шаблонов: %s", e)
                raise

    async def get_all_templates(
        self,
        limit: Optional[int] = None,
    ) -> List[MessageTemplate]:
        async with async_session() as session:
            try:
                query = select(MessageTemplate).options(
                    selectinload(MessageTemplate.media_items),
                    selectinload(MessageTemplate.category),
                )

                if limit is not None:
                    query = query.limit(limit)

                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                logger.error(f"Ошибка при получении шаблонов: {e}")
                raise

    async def get_templates_count(self) -> int:
        async with async_session() as session:
            try:
                query = select(func.count(MessageTemplate.id))
                result = await session.execute(query)
                return result.scalar_one()
            except Exception as e:
                logger.error("Ошибка при получении количества шаблонов: %s", e)
                raise

    async def get_templates_by_category_paginated(
        self,
        offset: int = 0,
        limit: int = 5,
        category_id: int = None,
    ) -> List[MessageTemplate]:
        async with async_session() as session:
            query = (
                select(MessageTemplate)
                .options(
                    selectinload(MessageTemplate.media_items),
                    selectinload(MessageTemplate.category),
                )
                .where(MessageTemplate.category_id == category_id)
                .order_by(MessageTemplate.title)
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def get_templates_paginated(
        self,
        offset: int = 0,
        limit: int = 5,
    ) -> List[MessageTemplate]:
        async with async_session() as session:
            query = (
                select(MessageTemplate)
                .options(
                    selectinload(MessageTemplate.media_items),
                    selectinload(MessageTemplate.category),
                )
                .order_by(MessageTemplate.title)
                .limit(limit)
                .offset(offset)
            )
            result = await session.execute(query)
            return result.scalars().all()

    async def get_template_by_id(self, template_id: int) -> Optional[MessageTemplate]:
        """Получаем быстрый ответ вместе с его медиа"""
        async with async_session() as session:
            try:
                query = (
                    select(MessageTemplate)
                    .options(
                        selectinload(MessageTemplate.media_items),
                        selectinload(MessageTemplate.category),
                    )
                    .where(MessageTemplate.id == template_id)
                )
                result = await session.execute(query)
                return result.scalar_one_or_none()
            except Exception as e:
                logger.error("Ошибка при получении шаблона по id: %s", e)
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
                logger.error("Ошибка при получении шаблонов по категории: %s", e)
                raise

    async def get_template_and_increase_usage_count(
        self,
        template_id: int,
        chat_id: str,
    ) -> Optional[MessageTemplate]:
        """
        Функция велосипед для автоподстановки шаблона в зависимости от того в какой
        чат было отправлено сообщение
        """
        async with async_session() as session:
            try:
                # Получаем базовый шаблон по ID
                base_query = (
                    select(MessageTemplate)
                    .where(MessageTemplate.id == template_id)
                    .options(
                        selectinload(MessageTemplate.media_items),
                        selectinload(MessageTemplate.category),
                    )
                )
                result = await session.execute(base_query)
                base_template = result.scalar_one_or_none()

                if not base_template:
                    logger.warning(f"Шаблон с ID={template_id} не найден")
                    return None

                # Проверяем что шаблон глоабльный
                if base_template.chat_id is None:
                    logger.debug(f"Шаблон '{base_template.title}' является глобальным")
                    template_to_use = base_template

                else:
                    # Ищем шаблон для конкретного чата но с тем же названием
                    chat_specific_query = (
                        select(MessageTemplate)
                        .join(ChatSession)
                        .where(
                            MessageTemplate.title == base_template.title,
                            ChatSession.chat_id == chat_id,
                        )
                        .options(
                            selectinload(MessageTemplate.media_items),
                            selectinload(MessageTemplate.category),
                        )
                    )
                    result = await session.execute(chat_specific_query)
                    chat_template = result.scalar_one_or_none()

                    template_to_use = chat_template

                if template_to_use:
                    # Увеличиваем счетчик использования
                    template_to_use.usage_count += 1
                    await session.commit()
                    await session.refresh(template_to_use)
                    logger.info(
                        f"Шаблон '{template_to_use.title}' был использован {template_to_use.usage_count} раз"
                    )

                return template_to_use
            except Exception as e:
                logger.error(f"Ошибка при обновлении шаблона: {e}")
                await session.rollback()
                raise

    async def delete_template(self, template_id: int) -> bool:
        async with async_session() as session:
            try:
                query = select(MessageTemplate).where(MessageTemplate.id == template_id)
                result = await session.execute(query)
                template = result.scalar_one_or_none()

                if template:
                    await session.delete(template)
                    await session.commit()
                    return True
                return False
            except Exception as e:
                logger.error(f"Ошибка при удалении шаблона: {e}")
                await session.rollback()
                raise

    async def update_template_title(self, template_id: int, new_title: str) -> bool:
        """Обновляет название шаблона"""
        async with async_session() as session:
            try:
                query = select(MessageTemplate).where(MessageTemplate.id == template_id)
                result = await session.execute(query)
                template = result.scalar_one_or_none()

                if template:
                    template.title = new_title
                    await session.commit()
                    logger.info(
                        f"Название шаблона {template_id} обновлено на '{new_title}'"
                    )
                    return True
                return False
            except Exception as e:
                logger.error(f"Ошибка при обновлении названия шаблона: {e}")
                await session.rollback()
                raise

    async def update_template_content(
        self, template_id: int, content_data: dict
    ) -> bool:
        """Обновляет содержимое шаблона"""
        from models import TemplateMedia

        async with async_session() as session:
            try:
                query = (
                    select(MessageTemplate)
                    .options(selectinload(MessageTemplate.media_items))
                    .where(MessageTemplate.id == template_id)
                )
                result = await session.execute(query)
                template = result.scalar_one_or_none()

                if template:
                    # Обновляем текстовое содержимое
                    if "text" in content_data:
                        template.content = content_data["text"]

                    # Удаляем старые медиа-файлы
                    for media_item in template.media_items:
                        await session.delete(media_item)

                    # Добавляем новые медиа-файлы
                    if "media_items" in content_data:
                        for position, media_data in enumerate(
                            content_data["media_items"]
                        ):
                            media_item = TemplateMedia(
                                template_id=template_id,
                                media_type=media_data["media_type"],
                                file_id=media_data["file_id"],
                                file_unique_id=media_data["file_unique_id"],
                                position=position,
                            )
                            session.add(media_item)

                    await session.commit()
                    logger.info(f"Содержимое шаблона {template_id} обновлено")
                    return True
                return False
            except Exception as e:
                logger.error(f"Ошибка при обновлении содержимого шаблона: {e}")
                await session.rollback()
                raise
