import logging
from typing import Optional

from sqlalchemy import func, select

from database.session import async_session
from models import Punishment, User

logger = logging.getLogger(__name__)


class PunishmentRepository:
    async def get_punishment_count(self, user_id: int) -> int:
        async with async_session() as session:
            try:
                logger.info(f"Подсчет количества наказаний для пользователя {user_id}")
                query = (
                    select(func.count())
                    .select_from(Punishment)
                    .where(Punishment.user_id == user_id)
                )
                result = await session.execute(query)
                count = result.scalar_one()
                logger.info(f"Найдено {count} наказаний для пользователя {user_id}")
                return count
            except Exception as e:
                logger.error(
                    f"Ошибка при подсчете наказаний для пользователя {user_id}: {e}"
                )
                raise

    async def get_current_punishment(self, user_tgid: str) -> Optional[Punishment]:
        async with async_session() as session:
            try:
                logger.info(
                    f"Получение текущего наказания для пользователя {user_tgid}"
                )
                query = (
                    select(Punishment)
                    .join(User, Punishment.user_id == User.id)
                    .where(User.tg_id == user_tgid)
                )

                result = await session.execute(query)
                punishment = result.scalar_one_or_none()

                if punishment:
                    logger.info(
                        f"Найдено текущее наказание для пользователя: {user_tgid}"
                    )
                else:
                    logger.info(
                        f"Текущее наказание для пользователя {user_tgid} не найдено"
                    )
                return punishment
            except Exception as e:
                logger.error(
                    f"Ошибка при получении текущего наказания для {user_tgid}: {e}"
                )
                return None

    async def update_punishment(self, punishment: Punishment) -> None:
        async with async_session() as session:
            try:
                logger.info(f"Обновление наказания {punishment.id}")
                session.add(punishment)
                await session.commit()
                await session.refresh(punishment)
                logger.info(f"Наказание {punishment.id} обновлено")
            except Exception as e:
                logger.error(f"Ошибка при обновлении наказания {punishment.id}: {e}")
                await session.rollback()
                raise e

    async def create_punishment(self, punishment: Punishment) -> Punishment:
        async with async_session() as session:
            try:
                logger.info("Создание нового наказания")
                session.add(punishment)
                await session.commit()
                await session.refresh(punishment)
                logger.info(f"Создано новое наказание с ID {punishment.id}")

                return punishment
            except Exception as e:
                logger.error(f"Ошибка при создании наказания: {e}")
                await session.rollback()
                raise e
