import logging
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.punishment_ladder import PunishmentLadder
from repositories.base import BaseRepository, transactional

logger = logging.getLogger(__name__)


class PunishmentLadderRepository(BaseRepository):
    @transactional
    async def get_punishment_by_step(
        self,
        session: AsyncSession,
        /,
        step: int,
        chat_id: str,
    ) -> Optional[PunishmentLadder]:
        """
        Получает ступень наказания для конкретного чата или глобальную.

        Сначала ищет настройку для конкретного chat_id. Если не находит,
        ищет глобальную настройку (где chat_id IS NULL).
        """
        chat_id = str(chat_id)
        logger.info("Получение наказания для шага %s в чате %s", step, chat_id)
        # Сначала ищем специфичную для чата настройку
        stmt_chat_specific = select(PunishmentLadder).where(
            PunishmentLadder.step == step, PunishmentLadder.chat_id == chat_id
        )
        result_chat_specific = await session.execute(stmt_chat_specific)
        punishment = result_chat_specific.scalar_one_or_none()

        if punishment:
            logger.info("Найдено наказание для чата по шагу %s.", step)
            return punishment

        # Если не нашли, ищем глобальную настройку
        logger.info(
            "Настройка для чата по шагу %s не найдена, ищем глобальную.",
            step,
        )
        stmt_global = select(PunishmentLadder).where(
            PunishmentLadder.step == step, PunishmentLadder.chat_id.is_(None)
        )
        result_global = await session.execute(stmt_global)
        punishment = result_global.scalar_one_or_none()
        logger.info(
            "Глобальное наказание для шага %s: найдено=%s",
            step,
            punishment is not None,
        )
        return punishment

    @transactional
    async def get_ladder_by_chat_id(self, session: AsyncSession, /, chat_id: str) -> list[PunishmentLadder]:
        """Возвращает всю лестницу наказаний для конкретного чата."""
        chat_id = str(chat_id)
        logger.info("Получение лестницы наказаний для чата %s", chat_id)
        stmt = (
            select(PunishmentLadder)
            .where(PunishmentLadder.chat_id == chat_id)
            .order_by(PunishmentLadder.step)
        )
        result = await session.execute(stmt)
        ladder = list(result.scalars().all())
        logger.info(
            "Найдено %d ступеней в лестнице для чата %s", len(ladder), chat_id
        )
        return ladder

    @transactional
    async def get_global_ladder(self, session: AsyncSession, /) -> list[PunishmentLadder]:
        """Возвращает глобальную лестницу наказаний."""
        logger.info("Получение глобальной лестницы наказаний.")
        stmt = (
            select(PunishmentLadder)
            .where(PunishmentLadder.chat_id.is_(None))
            .order_by(PunishmentLadder.step)
        )
        result = await session.execute(stmt)
        ladder = list(result.scalars().all())
        logger.info("Найдено %d ступеней в глобальной лестнице.", len(ladder))
        return ladder

    @transactional
    async def delete_ladder_by_chat_id(self, session: AsyncSession, /, chat_id: str) -> None:
        """Удаляет всю лестницу наказаний для конкретного чата."""
        chat_id = str(chat_id)
        logger.info("Удаление лестницы наказаний для чата %s", chat_id)
        stmt = delete(PunishmentLadder).where(
            PunishmentLadder.chat_id == chat_id
        )
        await session.execute(stmt)
        await session.commit()
        logger.info("Лестница наказаний для чата %s удалена.", chat_id)

    @transactional
    async def create_ladder(self, session: AsyncSession, /, steps: list[PunishmentLadder]) -> None:
        """Сохраняет новую лестницу наказаний."""
        logger.info("Создание новой лестницы наказаний.")
        session.add_all(steps)
        await session.commit()
        logger.info("Создана лестница наказаний с %d ступенями.", len(steps))
