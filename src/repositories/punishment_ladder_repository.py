import logging
from typing import Optional

from sqlalchemy import select

from database.session import DatabaseContextManager
from models.punishment_ladder import PunishmentLadder

logger = logging.getLogger(__name__)


class PunishmentLadderRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

    async def get_punishment_by_step(
        self,
        step: int,
        chat_id: str,
    ) -> Optional[PunishmentLadder]:
        """
        Получает ступень наказания для конкретного чата или глобальную.

        Сначала ищет настройку для конкретного chat_id. Если не находит,
        ищет глобальную настройку (где chat_id IS NULL).
        """
        async with self._db.session() as session:
            try:
                logger.info("Getting punishment for step %s in chat %s", step, chat_id)
                # Сначала ищем специфичную для чата настройку
                stmt_chat_specific = select(PunishmentLadder).where(
                    PunishmentLadder.step == step, PunishmentLadder.chat_id == chat_id
                )
                result_chat_specific = await session.execute(stmt_chat_specific)
                punishment = result_chat_specific.scalar_one_or_none()

                if punishment:
                    logger.info("Found chat-specific punishment for step %s.", step)
                    return punishment

                # Если не нашли, ищем глобальную настройку
                logger.info(
                    "No chat-specific punishment found for step %s, looking for global.",
                    step,
                )
                stmt_global = select(PunishmentLadder).where(
                    PunishmentLadder.step == step, PunishmentLadder.chat_id.is_(None)
                )
                result_global = await session.execute(stmt_global)
                punishment = result_global.scalar_one_or_none()
                logger.info(
                    "Found global punishment for step %s: %s",
                    step,
                    punishment is not None,
                )
                return punishment
            except Exception as e:
                logger.error(
                    "Error getting punishment by step %s for chat %s: %s",
                    step,
                    chat_id,
                    e,
                )
                raise

    async def get_ladder_by_chat_id(self, chat_id: str) -> list[PunishmentLadder]:
        """Возвращает всю лестницу наказаний для конкретного чата."""
        async with self._db.session() as session:
            try:
                logger.info("Getting punishment ladder for chat %s", chat_id)
                stmt = (
                    select(PunishmentLadder)
                    .where(PunishmentLadder.chat_id == chat_id)
                    .order_by(PunishmentLadder.step)
                )
                result = await session.execute(stmt)
                ladder = list(result.scalars().all())
                logger.info(
                    "Found %d steps in ladder for chat %s", len(ladder), chat_id
                )
                return ladder
            except Exception as e:
                logger.error("Error getting ladder for chat %s: %s", chat_id, e)
                raise

    async def get_global_ladder(self) -> list[PunishmentLadder]:
        """Возвращает глобальную лестницу наказаний."""
        async with self._db.session() as session:
            try:
                logger.info("Getting global punishment ladder.")
                stmt = (
                    select(PunishmentLadder)
                    .where(PunishmentLadder.chat_id.is_(None))
                    .order_by(PunishmentLadder.step)
                )
                result = await session.execute(stmt)
                ladder = list(result.scalars().all())
                logger.info("Found %d steps in global ladder.", len(ladder))
                return ladder
            except Exception as e:
                logger.error("Error getting global ladder: %s", e)
                raise
