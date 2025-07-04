import logging
from typing import Optional, Sequence

from sqlalchemy import select

from database.session import async_session
from models import QuickResponseCategory

logger = logging.getLogger(__name__)


class QuickResponseCategoryRepository:
    async def get_all_categories(self) -> Sequence[QuickResponseCategory]:
        """Получает список всех категорий шаблонов быстрых сообщений"""
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(QuickResponseCategory).order_by(
                        QuickResponseCategory.sort_order
                    )
                )

                categories = result.scalars().all()
                logger.info("Получено %d категорий", len(categories))

                return categories
            except Exception as e:
                logger.error("Ошибка при получении списка категорий: %s", e)
                return []

    async def get_last_category(self) -> Optional[QuickResponseCategory]:
        """Получаем последнюю созданную категорию"""
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(QuickResponseCategory).order_by(
                        QuickResponseCategory.sort_order.desc()
                    )
                )

                last_category = result.scalars().first()
                logger.info("Получена последняя категория: %s", last_category)

                return last_category
            except Exception as e:
                logger.error("Ошибка при получении последней категории: %s", str(e))
                return None

    async def get_category_by_id(self, id: int) -> Optional[QuickResponseCategory]:
        """Получаем категорию по имени"""
        async with async_session() as session:
            try:
                result = await session.execute(
                    select(QuickResponseCategory).where(QuickResponseCategory.id == id)
                )

                category = result.scalars().first()
                logger.info("Получена категория по имени: %s", category.name)

                return category
            except Exception as e:
                logger.error("Ошибка при получении категории c id: %d", str(e))
                return None

    async def create_category(self, name: str) -> Optional[QuickResponseCategory]:
        """Создаем новую категорию"""
        async with async_session() as session:
            try:
                last_category = await self.get_last_category()
                sort_order = last_category.sort_order + 1 if last_category else 1

                # Создаем новую категорию
                new_category = QuickResponseCategory(
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
