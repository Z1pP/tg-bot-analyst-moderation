import logging
from typing import Optional, Sequence

from sqlalchemy import select

from database.session import DatabaseContextManager
from models import TemplateCategory

logger = logging.getLogger(__name__)


class TemplateCategoryRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

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
            except Exception as e:
                logger.error("Ошибка при получении списка категорий: %s", e)
                return []

    async def get_category_by_name(self, name: str) -> Optional[TemplateCategory]:
        """Получаем категорию по имени"""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(TemplateCategory).where(TemplateCategory.name == name)
                )

                return result.scalars().first()
            except Exception as e:
                logger.error("Ошибка при получении категории c именем: %s", str(e))
                return None

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
            except Exception as e:
                logger.error("Ошибка при получении последней категории: %s", str(e))
                return None

    async def get_category_by_id(self, id: int) -> Optional[TemplateCategory]:
        """Получаем категорию по имени"""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(TemplateCategory).where(TemplateCategory.id == id)
                )

                category = result.scalars().first()
                logger.info("Получена категория по имени: %s", category.name)

                return category
            except Exception as e:
                logger.error("Ошибка при получении категории c id: %d", str(e))
                return None

    async def create_category(self, name: str) -> Optional[TemplateCategory]:
        """Создаем новую категорию"""
        async with self._db.session() as session:
            try:
                last_category = await self.get_last_category()
                sort_order = last_category.sort_order + 1 if last_category else 1

                # Создаем новую категорию
                new_category = TemplateCategory(
                    name=name,
                    sort_order=sort_order,
                )

                session.add(new_category)
                await session.commit()
                await session.refresh(new_category)

                logger.info('Была создана новая категория "%s"', new_category.name)

                return new_category
            except Exception as e:
                logger.error("Ошибка при создании новой категории: %s", str(e))
                raise Exception("Ошибка при создании репозитория")

    async def delete_category(self, category_id: int) -> None:
        """Удаляем категорию"""
        async with self._db.session() as session:
            try:
                category = await self.get_category_by_id(category_id)
                if category:
                    await session.delete(category)
                    await session.commit()
                    logger.info('Категория "%s" удалена', category.name)
                else:
                    logger.warning("Категория с id %d не найдена", category_id)
            except Exception as e:
                logger.error("Ошибка при удалении категории: %s", str(e))
                raise Exception("Ошибка при удалении категории")
            finally:
                await session.close()

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
                    f"Получено {len(categories)} категорий (страница {offset // limit + 1})"
                )
                return categories
            except Exception as e:
                logger.error(f"Ошибка при получении категорий с пагинацией: {e}")
                return []

    async def get_categories_count(self) -> int:
        """Получает общее количество категорий."""
        async with self._db.session() as session:
            try:
                from sqlalchemy import func

                result = await session.execute(select(func.count(TemplateCategory.id)))
                count = result.scalar()
                logger.info(f"Общее количество категорий: {count}")
                return count or 0
            except Exception as e:
                logger.error(f"Ошибка при подсчете категорий: {e}")
                return 0

    async def update_category_name(self, category_id: int, new_name: str) -> bool:
        """Обновляет название категории"""
        async with self._db.session() as session:
            try:
                query = select(TemplateCategory).where(
                    TemplateCategory.id == category_id
                )
                result = await session.execute(query)
                category = result.scalar_one_or_none()

                if category:
                    category.name = new_name
                    await session.commit()
                    logger.info(
                        f"Название категории {category_id} обновлено на '{new_name}'"
                    )
                    return True
                return False
            except Exception as e:
                logger.error(f"Ошибка при обновлении названия категории: {e}")
                await session.rollback()
                raise
