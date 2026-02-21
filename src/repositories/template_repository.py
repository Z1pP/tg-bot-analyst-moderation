import logging
from typing import Any, List, Optional

from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from exceptions import DatabaseException
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

                logger.info("Создан шаблон с id=%s", new_template.id)

                return new_template
            except SQLAlchemyError as e:
                logger.error("Ошибка при создании шаблона: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "create_template", "original": str(e)}
                ) from e

    async def get_templates_by_query(self, query: str) -> List[MessageTemplate]:
        """Ищет шаблоны по подстроке в названии (уникальные по title)."""
        async with self._db.session() as session:
            try:
                # Подзапрос для получения минимальных ID уникальных заголовков
                search_pattern = f"%{query}%"
                subquery = (
                    select(
                        MessageTemplate.title,
                        func.min(MessageTemplate.id).label("min_id"),
                    )
                    .where(MessageTemplate.title.ilike(search_pattern))
                    .group_by(MessageTemplate.title)
                    .subquery()
                )

                # Основной запрос — выбираем только записи с минимальными ID
                stmt = (
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

                result = await session.execute(stmt)
                return list(result.scalars().all())

            except SQLAlchemyError as e:
                logger.error("Ошибка при поиске шаблонов: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_templates_by_query", "original": str(e)}
                ) from e

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
                return result.scalar() or 0
            except SQLAlchemyError as e:
                logger.error("Ошибка при получении количества шаблонов: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_templates_count", "original": str(e)}
                ) from e

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
                return list(result.scalars().all())
            except SQLAlchemyError as e:
                logger.error("Ошибка при получении списка шаблонов: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_templates_paginated", "original": str(e)}
                ) from e

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
            except SQLAlchemyError as e:
                logger.error("Ошибка при получении шаблона по id: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_template_by_id", "original": str(e)}
                ) from e

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
            except SQLAlchemyError as e:
                logger.error("Ошибка при получении и обновлении шаблона: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_template_and_increase_usage_count", "original": str(e)}
                ) from e

    async def _get_effective_template(
        self,
        session: AsyncSession,
        template_id: int,
        chat_tg_id: str,
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
            except SQLAlchemyError as e:
                logger.error("Ошибка при удалении шаблона: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "delete_template", "original": str(e)}
                ) from e

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
                        "Название шаблона %s обновлено на '%s'",
                        template_id,
                        new_title,
                    )
                    return True
                return False
            except SQLAlchemyError as e:
                logger.error("Ошибка при обновлении названия шаблона: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "update_template_title", "original": str(e)}
                ) from e

    async def _remove_conflicting_media_in_other_templates(
        self,
        session: AsyncSession,
        template_id: int,
        unique_ids: set[str],
    ) -> None:
        """Удаляет медиа с указанными file_unique_id в других шаблонах."""
        if not unique_ids:
            return
        stmt = select(TemplateMedia).where(
            TemplateMedia.file_unique_id.in_(unique_ids),
            TemplateMedia.template_id != template_id,
        )
        result = await session.execute(stmt)
        for media in result.scalars().all():
            await session.delete(media)
        await session.flush()

    def _append_media_items_from_data(
        self, template: MessageTemplate, media_items_data: list[dict[str, Any]]
    ) -> None:
        """Добавляет к шаблону медиа-элементы из списка словарей."""
        for position, media_data in enumerate(media_items_data):
            media_item = TemplateMedia(
                media_type=media_data["media_type"],
                file_id=media_data["file_id"],
                file_unique_id=media_data["file_unique_id"],
                position=position,
            )
            template.media_items.append(media_item)

    async def update_template_content(
        self,
        template_id: int,
        content_data: dict[str, Any],
    ) -> bool:
        """Обновляет содержимое шаблона (текст и медиа)."""
        async with self._db.session() as session:
            try:
                stmt = (
                    select(MessageTemplate)
                    .options(selectinload(MessageTemplate.media_items))
                    .where(MessageTemplate.id == template_id)
                )
                result = await session.execute(stmt)
                template = result.scalar_one_or_none()

                if not template:
                    return False

                template.media_items.clear()
                await session.flush()

                media_items = content_data.get("media_items") or []
                unique_ids = {item["file_unique_id"] for item in media_items}
                await self._remove_conflicting_media_in_other_templates(
                    session, template_id, unique_ids
                )

                if "text" in content_data:
                    template.content = content_data["text"]

                if media_items:
                    self._append_media_items_from_data(template, media_items)

                await session.commit()
                logger.info("Содержимое шаблона %s обновлено", template_id)
                return True
            except SQLAlchemyError as e:
                logger.error("Ошибка при обновлении содержимого шаблона: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "update_template_content", "original": str(e)}
                ) from e
