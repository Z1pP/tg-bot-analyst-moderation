import logging
from typing import Optional, Sequence

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import TemplateCategory
from repositories.base import BaseRepository, transactional

logger = logging.getLogger(__name__)


class TemplateCategoryRepository(BaseRepository):
    @transactional
    async def get_all_categories(self, session: AsyncSession, /) -> Sequence[TemplateCategory]:
        """Получает список всех категорий шаблонов быстрых сообщений"""
        result = await session.execute(
            select(TemplateCategory).order_by(TemplateCategory.sort_order)
        )

        categories = result.scalars().all()
        logger.info("Получено %d категорий", len(categories))

        return categories

    @transactional
    async def get_last_category(self, session: AsyncSession, /) -> Optional[TemplateCategory]:
        """Получаем последнюю созданную категорию"""
        result = await session.execute(
            select(TemplateCategory).order_by(
                TemplateCategory.sort_order.desc()
            )
        )

        last_category = result.scalars().first()
        logger.info("Получена последняя категория: %s", last_category)

        return last_category

    @transactional
    async def get_category_by_id(self, session: AsyncSession, /, category_id: int) -> Optional[TemplateCategory]:
        """Получает категорию по идентификатору."""
        result = await session.execute(
            select(TemplateCategory).where(TemplateCategory.id == category_id)
        )

        category = result.scalars().first()
        if category:
            logger.info("Получена категория по id: %s", category.name)

        return category

    @transactional
    async def create_category(self, session: AsyncSession, /, name: str) -> Optional[TemplateCategory]:
        """Создаем новую категорию"""
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

    @transactional
    async def delete_category(self, session: AsyncSession, /, category_id: int) -> None:
        """Удаляем категорию"""
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

    @transactional
    async def get_categories_paginated(
        self, session: AsyncSession, /, limit: int = 5, offset: int = 0
    ) -> Sequence[TemplateCategory]:
        """Получает категории с пагинацией."""
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

    @transactional
    async def get_categories_count(self, session: AsyncSession, /) -> int:
        """Получает общее количество категорий."""
        result = await session.execute(select(func.count(TemplateCategory.id)))
        count = result.scalar()
        logger.info("Общее количество категорий: %s", count)
        return count or 0

    @transactional
    async def update_category_name(
        self, session: AsyncSession, /, category_id: int, new_name: str
    ) -> Optional[TemplateCategory]:
        """Обновляет название категории."""
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
