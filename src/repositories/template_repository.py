import logging
from typing import List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import selectinload

from models import ChatSession, MessageTemplate, TemplateMedia
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class MessageTemplateRepository(BaseRepository):
    async def create_template(
        self,
        title: str,
        content: str,
        category_id: int,
        author_id: int,
        chat_id: Optional[int] = None,
    ) -> MessageTemplate:
        async with self._db.session() as session:
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
        async with self._db.session() as session:
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

    async def get_templates_count(
        self,
        category_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        global_only: bool = False,
    ) -> int:
        """Получает количество шаблонов с учетом фильтров."""
        async with self._db.session() as session:
            try:
                query = select(func.count(MessageTemplate.id))

                if global_only:
                    query = query.where(MessageTemplate.chat_id.is_(None))
                elif chat_id is not None:
                    query = query.where(MessageTemplate.chat_id == chat_id)

                if category_id is not None:
                    query = query.where(MessageTemplate.category_id == category_id)

                result = await session.execute(query)
                return result.scalar_one()
            except Exception as e:
                logger.error("Ошибка при получении количества шаблонов: %s", e)
                raise

    async def get_templates_paginated(
        self,
        offset: int = 0,
        limit: int = 5,
        category_id: Optional[int] = None,
        chat_id: Optional[int] = None,
        global_only: bool = False,
    ) -> List[MessageTemplate]:
        """Получает список шаблонов с пагинацией и учетом фильтров."""
        async with self._db.session() as session:
            try:
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

                if global_only:
                    query = query.where(MessageTemplate.chat_id.is_(None))
                elif chat_id is not None:
                    query = query.where(MessageTemplate.chat_id == chat_id)

                if category_id is not None:
                    query = query.where(MessageTemplate.category_id == category_id)

                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                logger.error("Ошибка при получении списка шаблонов: %s", e)
                raise

    async def get_template_by_id(self, template_id: int) -> Optional[MessageTemplate]:
        """Получаем быстрый ответ вместе с его медиа"""
        async with self._db.session() as session:
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

    async def get_template_and_increase_usage_count(
        self,
        template_id: int,
        chat_id: str,
    ) -> Optional[MessageTemplate]:
        """
        Находит подходящий шаблон (с учетом переопределений для чата)
        и увеличивает счетчик его использования.
        """
        async with self._db.session() as session:
            try:
                template = await self._get_effective_template(
                    session, template_id, chat_id
                )

                if template:
                    template.usage_count += 1
                    await session.commit()
                    logger.info(
                        "Шаблон '%s' (ID=%d) использован %d раз",
                        template.title,
                        template.id,
                        template.usage_count,
                    )
                return template
            except Exception as e:
                logger.error("Ошибка при получении и обновлении шаблона: %s", e)
                await session.rollback()
                raise

    async def _get_effective_template(
        self, session, template_id: int, chat_tg_id: str
    ) -> Optional[MessageTemplate]:
        """
        Находит эффективный шаблон с использованием JOIN.
        Если базовый шаблон глобальный - возвращает его.
        Если базовый шаблон привязан к чату - ищет шаблон с тем же названием в целевом чате.
        """
        # Подзапрос для получения данных базового шаблона
        base_template_stmt = (
            select(MessageTemplate.title, MessageTemplate.chat_id)
            .where(MessageTemplate.id == template_id)
            .subquery()
        )

        # Основной запрос: ищем либо сам глобальный шаблон,
        # либо его переопределение в конкретном чате по названию
        query = (
            select(MessageTemplate)
            .join(
                base_template_stmt,
                MessageTemplate.title == base_template_stmt.c.title,
            )
            .outerjoin(ChatSession, MessageTemplate.chat_id == ChatSession.id)
            .where(
                or_(
                    # Если базовый шаблон глобальный - возвращаем его (по ID)
                    and_(
                        MessageTemplate.id == template_id,
                        base_template_stmt.c.chat_id.is_(None),
                    ),
                    # Если базовый не глобальный - ищем шаблон с тем же названием в целевом чате
                    and_(
                        ChatSession.chat_id == chat_tg_id,
                        base_template_stmt.c.chat_id.is_not(None),
                    ),
                )
            )
            .options(
                selectinload(MessageTemplate.media_items),
                selectinload(MessageTemplate.category),
            )
        )

        result = await session.execute(query)
        return result.scalar_one_or_none()

    async def delete_template(self, template_id: int) -> bool:
        async with self._db.session() as session:
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
        async with self._db.session() as session:
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
        self,
        template_id: int,
        content_data: dict,
    ) -> bool:
        """Обновляет содержимое шаблона"""

        async with self._db.session() as session:
            try:
                # Сначала загружаем шаблон и очищаем его медиа
                query = (
                    select(MessageTemplate)
                    .options(selectinload(MessageTemplate.media_items))
                    .where(MessageTemplate.id == template_id)
                )
                result = await session.execute(query)
                template = result.scalar_one_or_none()

                if not template:
                    return False

                # Очищаем старые медиа текущего шаблона
                template.media_items.clear()
                await session.flush()  # Фиксируем удаление старых медиа

                # Теперь удаляем медиа с таким же unique_id из ДРУГИХ шаблонов
                if "media_items" in content_data and content_data["media_items"]:
                    unique_ids_to_update = {
                        item["file_unique_id"] for item in content_data["media_items"]
                    }

                    if unique_ids_to_update:
                        stmt = select(TemplateMedia).where(
                            TemplateMedia.file_unique_id.in_(unique_ids_to_update),
                            TemplateMedia.template_id != template_id,
                        )
                        result = await session.execute(stmt)
                        conflicting_media = result.scalars().all()

                        for media in conflicting_media:
                            await session.delete(media)
                        await session.flush()  # Фиксируем удаление конфликтующих медиа

                # Обновляем текстовое содержимое
                if "text" in content_data:
                    template.content = content_data["text"]

                # Добавляем новые медиа-файлы
                if "media_items" in content_data:
                    for position, media_data in enumerate(content_data["media_items"]):
                        media_item = TemplateMedia(
                            media_type=media_data["media_type"],
                            file_id=media_data["file_id"],
                            file_unique_id=media_data["file_unique_id"],
                            position=position,
                        )
                        template.media_items.append(media_item)

                await session.commit()
                logger.info(f"Содержимое шаблона {template_id} обновлено")
                return True
            except Exception as e:
                logger.error(f"Ошибка при обновлении содержимого шаблона: {e}")
                await session.rollback()
                raise
