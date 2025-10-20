import logging
from typing import Optional

from sqlalchemy import delete, func, select
from sqlalchemy.orm import joinedload

from database.session import DatabaseContextManager
from models import Punishment, User

logger = logging.getLogger(__name__)


class PunishmentRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

    async def get_punishment_count(self, user_id: int) -> int:
        async with self._db.session() as session:
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

    async def get_current_punishment(
        self, user_id: int, chat_id: int
    ) -> Optional[Punishment]:
        async with self._db.session() as session:
            try:
                query = (
                    select(Punishment)
                    .options(joinedload(Punishment.user))
                    .where(Punishment.user_id == user_id, Punishment.chat_id == chat_id)
                    .order_by(Punishment.created_at.desc())
                    .limit(1)
                )

                result = await session.execute(query)
                punishment = result.scalar_one_or_none()

                if punishment:
                    logger.info(
                        "Найдено текущее наказание для пользователя %s",
                        punishment.user.username,
                    )
                else:
                    logger.info(
                        "Текущее наказание для пользователя %s не найдено",
                        punishment.user.username,
                    )
                return punishment
            except Exception as e:
                logger.error(
                    "Ошибка при получении текущего наказания для %s: %s",
                    user_id,
                    e,
                )
                return None

    async def update_punishment(self, punishment: Punishment) -> None:
        async with self._db.session() as session:
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
        async with self._db.session() as session:
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

    async def delete_user_punishments(self, user_id: int, chat_id: int) -> int:
        """Удаляет все наказания пользователя в указанном чате."""
        async with self._db.session() as session:
            try:
                query = delete(Punishment).where(
                    Punishment.user_id == user_id, Punishment.chat_id == chat_id
                )
                result = await session.execute(query)
                await session.commit()

                deleted_count = result.rowcount
                logger.info(
                    "Удалено %d наказаний для user_id=%s в chat_id=%s",
                    deleted_count,
                    user_id,
                    chat_id,
                )
                return deleted_count
            except Exception as e:
                logger.error(
                    "Ошибка удаления наказаний для user_id=%s в chat_id=%s: %s",
                    user_id,
                    chat_id,
                    e,
                )
                await session.rollback()
                raise

    async def count_punishments(self, user_id: int, chat_id: int) -> int:
        """Подсчитывает количество наказаний пользователя в указанном чате."""
        async with self._db.session() as session:
            try:
                query = select(func.count(Punishment.id)).where(
                    Punishment.user_id == user_id, Punishment.chat_id == chat_id
                )
                result = await session.execute(query)
                return result.scalar() or 0
            except Exception as e:
                logger.error(
                    "Ошибка подсчета наказаний для user_id=%s в chat_id=%s: %s",
                    user_id,
                    chat_id,
                    e,
                )
                raise

    async def delete_last_punishment(self, user_id: int, chat_id: int) -> bool:
        """Удаляет последнее наказание пользователя в чате."""
        async with self._db.session() as session:
            try:
                result = await session.execute(
                    select(Punishment)
                    .where(Punishment.user_id == user_id, Punishment.chat_id == chat_id)
                    .order_by(Punishment.created_at.desc())
                    .limit(1)
                )
                punishment = result.scalar_one_or_none()

                if punishment:
                    await session.delete(punishment)
                    await session.commit()
                    logger.info(
                        "Удалено последнее наказание для user_id=%s в chat_id=%s",
                        user_id,
                        chat_id,
                    )
                    return True
                return False
            except Exception as e:
                logger.error(
                    "Ошибка удаления последнего наказания для user_id=%s в chat_id=%s: %s",
                    user_id,
                    chat_id,
                    e,
                )
                await session.rollback()
                raise
