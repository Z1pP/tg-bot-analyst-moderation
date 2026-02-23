import logging
from datetime import datetime

from sqlalchemy import Date, delete, func, select
from sqlalchemy import cast as sa_cast
from sqlalchemy.exc import SQLAlchemyError

from constants.punishment import PunishmentType
from exceptions import DatabaseException
from models import Punishment
from repositories.base import BaseRepository

logger = logging.getLogger(__name__)


class PunishmentRepository(BaseRepository):
    async def count_punishments(self, user_id: int, chat_id: int | None = None) -> int:
        """Подсчитывает количество наказаний пользователя (опционально в указанном чате)."""
        async with self._db.session() as session:
            try:
                query = select(func.count(Punishment.id)).where(
                    Punishment.user_id == user_id
                )
                if chat_id is not None:
                    query = query.where(Punishment.chat_id == chat_id)

                result = await session.execute(query)
                count = result.scalar() or 0
                return count
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка подсчета наказаний для user_id=%s (chat_id=%s): %s",
                    user_id,
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "count_punishments", "original": str(e)}
                ) from e

    async def create_punishment(self, punishment: Punishment) -> Punishment:
        async with self._db.session() as session:
            try:
                logger.info("Создание нового наказания")
                session.add(punishment)
                await session.commit()
                await session.refresh(punishment)
                logger.info("Создано новое наказание с ID %s", punishment.id)

                return punishment
            except SQLAlchemyError as e:
                logger.error("Ошибка при создании наказания: %s", e, exc_info=True)
                await session.rollback()
                raise DatabaseException(
                    details={"context": "create_punishment", "original": str(e)}
                ) from e

    async def delete_user_punishments(self, user_id: int, chat_id: int) -> int:
        """Удаляет все наказания пользователя в указанном чате."""
        async with self._db.session() as session:
            try:
                query = delete(Punishment).where(
                    Punishment.user_id == user_id, Punishment.chat_id == chat_id
                )
                result = await session.execute(query)
                await session.commit()

                deleted_count: int = getattr(result, "rowcount", 0) or 0
                logger.info(
                    "Удалено %d наказаний для user_id=%s в chat_id=%s",
                    deleted_count,
                    user_id,
                    chat_id,
                )
                return deleted_count
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка удаления наказаний для user_id=%s в chat_id=%s: %s",
                    user_id,
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "delete_user_punishments", "original": str(e)}
                ) from e

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
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка удаления последнего наказания для user_id=%s в chat_id=%s: %s",
                    user_id,
                    chat_id,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={"context": "delete_last_punishment", "original": str(e)}
                ) from e

    async def get_punishment_counts_by_moderator(
        self,
        moderator_id: int,
        start_date: datetime,
        end_date: datetime,
        chat_ids: list[int] | None = None,
    ) -> dict[str, int]:
        """
        Возвращает количество варнов и банов, выданных модератором за период.
        """
        async with self._db.session() as session:
            try:
                query = select(
                    Punishment.punishment_type, func.count(Punishment.id)
                ).where(
                    Punishment.punished_by_id == moderator_id,
                    Punishment.created_at.between(start_date, end_date),
                )

                if chat_ids:
                    query = query.where(Punishment.chat_id.in_(chat_ids))

                query = query.group_by(Punishment.punishment_type)

                result = await session.execute(query)
                counts = {row[0]: row[1] for row in result.all()}

                return {
                    "warns": counts.get(PunishmentType.WARNING, 0),
                    "bans": counts.get(PunishmentType.BAN, 0),
                }
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при получении статистики наказаний модератора: %s",
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={
                        "context": "get_punishment_counts_by_moderator",
                        "original": str(e),
                    }
                ) from e

    async def get_punishment_counts_by_moderators(
        self,
        moderator_ids: list[int],
        start_date: datetime,
        end_date: datetime,
    ) -> dict[int, dict[str, int]]:
        """
        Возвращает количество варнов и банов для списка модераторов за период (batch query).
        """
        async with self._db.session() as session:
            try:
                query = (
                    select(
                        Punishment.punished_by_id,
                        Punishment.punishment_type,
                        func.count(Punishment.id),
                    )
                    .where(
                        Punishment.punished_by_id.in_(moderator_ids),
                        Punishment.created_at.between(start_date, end_date),
                    )
                    .group_by(Punishment.punished_by_id, Punishment.punishment_type)
                )

                result = await session.execute(query)
                rows = result.all()

                stats = {mod_id: {"warns": 0, "bans": 0} for mod_id in moderator_ids}
                for mod_id, p_type, count in rows:
                    if mod_id not in stats:
                        continue
                    if p_type == PunishmentType.WARNING:
                        stats[mod_id]["warns"] = count
                    elif p_type == PunishmentType.BAN:
                        stats[mod_id]["bans"] = count

                return stats
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при получении групповой статистики наказаний модераторов: %s",
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={
                        "context": "get_punishment_counts_by_moderators",
                        "original": str(e),
                    }
                ) from e

    async def get_daily_punishment_counts(
        self, start: datetime, end: datetime
    ) -> dict[str, dict[str, int]]:
        """
        Возвращает количество варнов и банов, сгруппированных по дате за указанный период.
        Результат: {date_str: {"warns": N, "bans": N}}, где date_str = "YYYY-MM-DD".
        """
        async with self._db.session() as session:
            try:
                query = (
                    select(
                        sa_cast(Punishment.created_at, Date).label("day"),
                        Punishment.punishment_type,
                        func.count(Punishment.id).label("cnt"),
                    )
                    .where(Punishment.created_at.between(start, end))
                    .group_by(
                        sa_cast(Punishment.created_at, Date), Punishment.punishment_type
                    )
                )
                result = await session.execute(query)
                rows = result.all()

                counts: dict[str, dict[str, int]] = {}
                for day, p_type, cnt in rows:
                    date_str = str(day)
                    if date_str not in counts:
                        counts[date_str] = {"warns": 0, "bans": 0}
                    if p_type == PunishmentType.WARNING:
                        counts[date_str]["warns"] = cnt
                    elif p_type == PunishmentType.BAN:
                        counts[date_str]["bans"] = cnt

                return counts
            except SQLAlchemyError as e:
                logger.error(
                    "Ошибка при получении статистики наказаний по дням за %s — %s: %s",
                    start,
                    end,
                    e,
                    exc_info=True,
                )
                await session.rollback()
                raise DatabaseException(
                    details={
                        "context": "get_daily_punishment_counts",
                        "original": str(e),
                    }
                ) from e
