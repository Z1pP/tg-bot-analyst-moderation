import logging
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from exceptions import DatabaseException
from models import TemplateCategory
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class TemplateCategoryRepository(BaseRepository):
    async def get_all_categories(self) -> Sequence[TemplateCategory]:
        """Получает список всех категорий шаблонов быстрых сообщений"""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(TemplateCategory).order_by(TemplateCategory.sort_order)
                )

                categories = result.scalars().all()
                logger.info("Получено %d категорий", len(categories))

                return categories
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при получении списка категорий: %s", e, exc_info=True
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_all_categories", "original": str(e)}
                ) from e

    async def get_last_category(self) -> Optional[TemplateCategory]:
        """Получаем последнюю созданную категорию"""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(TemplateCategory).order_by(
                        TemplateCategory.sort_order.desc()
                    )
                )

                last_category = result.scalars().first()
                logger.info("Получена последняя категория: %s", last_category)

                return last_category
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при получении последней категории: %s", e, exc_info=True
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_last_category", "original": str(e)}
                ) from e

    async def get_category_by_id(self, category_id: int) -> Optional[TemplateCategory]:
        """Получает категорию по идентификатору."""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(TemplateCategory).where(TemplateCategory.id == category_id)
                )

                category = result.scalars().first()
                if category:
                    logger.info("Получена категория по id: %s", category.name)

                return category
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при получении категории по id: %s", e, exc_info=True
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_category_by_id", "original": str(e)}
                ) from e

    async def create_category(self, name: str) -> Optional[TemplateCategory]:
        """Создаем новую категорию"""
        async with self._db.session() as session:
            try:
                last_result = await session.execute(
                    select(TemplateCategory)
                    .order_by(TemplateCategory.sort_order.desc())
                    .limit(1)
                )
                last_category = last_result.scalars().first()
                sort_order = last_category.sort_order + 1 if last_category else 1

                new_category = TemplateCategory(
                    name=name,
                    sort_order=sort_order,
                )

                session.add(new_category)
                await session.commit()
                await session.refresh(new_category)

                logger.info('Была создана новая категория "%s"', new_category.name)

                return new_category
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при создании новой категории: %s", e, exc_info=True
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "create_category", "original": str(e)},
                ) from e

    async def delete_category(self, category_id: int) -> None:
        """Удаляем категорию"""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(TemplateCategory).where(TemplateCategory.id == category_id)
                )
                category = result.scalar_one_or_none()
                if category:
                    await session.delete(category)
                    await session.commit()
                    logger.info('Категория "%s" удалена', category.name)
                else:
                    logger.warning("Категория с id %d не найдена", category_id)
            except SQLAlchemyError as e:
                logger.error("Ошибка при удалении категории: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "delete_category", "original": str(e)},
                ) from e

    async def get_categories_paginated(
        self, limit: int = 5, offset: int = 0
    ) -> Sequence[TemplateCategory]:
        """Получает категории с пагинацией."""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(TemplateCategory)
                    .order_by(TemplateCategory.sort_order)
                    .limit(limit)
                    .offset(offset)
                )
                categories = result.scalars().all()
                logger.info(
                    "Получено %d категорий (страница %d)",
                    len(categories),
                    offset // limit + 1,
                )
                return categories
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при получении категорий с пагинацией: %s", e, exc_info=True
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_categories_paginated", "original": str(e)}
                ) from e

    async def get_categories_count(self) -> int:
        """Получает общее количество категорий."""
        async with self._db.session() as session:
            try:
                result = await session.execute(select(func.count(TemplateCategory.id)))
                count = result.scalar()
                logger.info("Общее количество категорий: %s", count)
                return count or 0
            except SQLAlchemyError as e:
                logger.error("Ошибка при подсчете категорий: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "get_categories_count", "original": str(e)}
                ) from e

    async def update_category_name(
        self, category_id: int, new_name: str
    ) -> Optional[TemplateCategory]:
        """Обновляет название категории."""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(TemplateCategory).where(TemplateCategory.id == category_id)
                )
                category = result.scalar_one_or_none()
                if not category:
                    logger.warning("Категория с id %d не найдена", category_id)
                    return None

                category.name = new_name
                await session.commit()
                await session.refresh(category)

                logger.info(
                    "Название категории %d обновлено на '%s'",
                    category_id,
                    new_name,
                )
                return category
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при обновлении названия категории: %s", e, exc_info=True
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "update_category_name", "original": str(e)}
                ) from e
