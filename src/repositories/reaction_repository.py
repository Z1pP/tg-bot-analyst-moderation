import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from dto.buffer import BufferedReactionDTO
from dto.daily_activity import PopularReactionDTO, UserReactionActivityDTO
from dto.reaction import MessageReactionDTO
from models import MessageReaction, User
from repositories.base import BaseRepository, transactional
from utils.date_utils import validate_and_normalize_period

logger = logging.getLogger(__name__)


class MessageReactionRepository(BaseRepository):
    @transactional
    async def add_reaction(self, session: AsyncSession, /, dto: MessageReactionDTO) -> MessageReaction:
        logger.info(
            "Создание реакции: пользователь %s, сообщение %s, эмодзи %s",
            dto.user_tgid,
            dto.message_id,
            dto.emoji,
        )

        # Внутренние id чата и пользователя (FK); при необходимости резолв из dto.chat_tgid/dto.user_tgid
        chat_id = getattr(dto, "chat_id", int(dto.chat_tgid))
        user_id = getattr(dto, "user_id", int(dto.user_tgid))
        reaction = MessageReaction(
            chat_id=chat_id,
            user_id=user_id,
            message_id=dto.message_id,
            action=dto.action,
            emoji=dto.emoji,
            message_url=dto.message_url,
        )
        session.add(reaction)
        await session.commit()
        await session.refresh(reaction)

        logger.info("Реакция успешно создана с ID: %s", reaction.id)
        return reaction

    @transactional
    async def get_reactions_by_chat_and_period(
        self,
        session: AsyncSession,
        /,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
        tracked_user_ids: Optional[list[int]] = None,
    ) -> List[MessageReaction]:
        logger.debug("Получение реакций для чата с ID=%s", chat_id)

        query = (
            select(MessageReaction)
            .options(joinedload(MessageReaction.user))
            .where(
                MessageReaction.chat_id == chat_id,
                MessageReaction.created_at.between(start_date, end_date),
            )
        )

        # Фильтруем только по отслеживаемым пользователям
        if tracked_user_ids:
            query = query.where(MessageReaction.user_id.in_(tracked_user_ids))
        result = await session.execute(query)
        reactions = list(result.scalars().all())

        logger.info(
            "Найдено %d реакций для чата с ID=%s", len(reactions), chat_id
        )
        return reactions

    @transactional
    async def get_reactions_by_user_and_period_for_users(
        self,
        session: AsyncSession,
        /,
        user_ids: list[int],
        start_date: datetime,
        end_date: datetime,
    ) -> List[MessageReaction]:
        """Получает реакции для списка пользователей за период."""
        if not user_ids:
            return []

        logger.debug("Получение реакций для списка пользователей")

        query = (
            select(MessageReaction)
            .options(joinedload(MessageReaction.user))
            .where(
                MessageReaction.user_id.in_(user_ids),
                MessageReaction.created_at.between(start_date, end_date),
            )
        )
        result = await session.execute(query)
        reactions = list(result.scalars().all())

        logger.info(
            "Найдено %d реакций для пользователей (%d)",
            len(reactions),
            len(user_ids),
        )
        return reactions

    @transactional
    async def get_daily_top_reactors(
        self,
        session: AsyncSession,
        /,
        chat_id: int,
        date: datetime | None = None,
        limit: int = 10,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> List[UserReactionActivityDTO]:
        """
        Получает топ пользователей по количеству реакций за период.
        """
        start_date, end_date = validate_and_normalize_period(
            date, start_date, end_date
        )

        query = (
            select(
                MessageReaction.user_id,
                User.username,
                func.count(MessageReaction.id).label("reaction_count"),
            )
            .join(User, MessageReaction.user_id == User.id, isouter=True)
            .where(
                MessageReaction.chat_id == chat_id,
                MessageReaction.created_at.between(start_date, end_date),
            )
            .group_by(MessageReaction.user_id, User.username)
            .order_by(func.count(MessageReaction.id).desc())
            .limit(limit)
        )

        result = await session.execute(query)
        rows = result.fetchall()

        top_reactors = []
        for rank, row in enumerate(rows, 1):
            top_reactors.append(
                UserReactionActivityDTO(
                    user_id=row.user_id,
                    username=row.username or f"User ID: {row.user_id}",
                    reaction_count=row.reaction_count,
                    rank=rank,
                )
            )

        logger.info(
            "Получен топ-%d по реакциям для chat_id=%s за период %s - %s",
            len(top_reactors),
            chat_id,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        )
        return top_reactors


    @transactional
    async def get_daily_popular_reactions(
        self,
        session: AsyncSession,
        /,
        chat_id: int,
        date: datetime | None = None,
        limit: int = 3,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> List[PopularReactionDTO]:
        """
        Получает самые популярные реакции за период.
        """
        start_date, end_date = validate_and_normalize_period(
            date, start_date, end_date
        )

        query = (
            select(
                MessageReaction.emoji,
                func.count(MessageReaction.id).label("count"),
            )
            .where(
                MessageReaction.chat_id == chat_id,
                MessageReaction.action == "added",
                MessageReaction.created_at.between(start_date, end_date),
            )
            .group_by(MessageReaction.emoji)
            .order_by(func.count(MessageReaction.id).desc())
            .limit(limit)
        )

        result = await session.execute(query)
        rows = result.fetchall()

        popular_reactions: List[PopularReactionDTO] = []
        for rank, row in enumerate(rows, 1):
            count_val: int = (
                row._mapping["count"]
                if hasattr(row, "_mapping")
                else int(row[1])
            )
            popular_reactions.append(
                PopularReactionDTO(emoji=row.emoji, count=count_val, rank=rank)
            )

        logger.info(
            "Получено %d популярных реакций для chat_id=%s за период %s - %s",
            len(popular_reactions),
            chat_id,
            start_date.strftime("%Y-%m-%d"),
            end_date.strftime("%Y-%m-%d"),
        )
        return popular_reactions


    @transactional
    async def get_reactions_by_user_and_period_and_chats(
        self,
        session: AsyncSession,
        /,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        chat_ids: List[int],
    ) -> List[MessageReaction]:
        """Получает реакции пользователя в определенных чатах за период"""
        query = (
            select(MessageReaction)
            .options(joinedload(MessageReaction.user))
            .where(
                MessageReaction.user_id == user_id,
                MessageReaction.chat_id.in_(chat_ids),
                MessageReaction.created_at.between(start_date, end_date),
            )
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    async def bulk_add_reactions(self, dtos: List[BufferedReactionDTO]) -> int:
        """
        Массовое добавление реакций с защитой от дубликатов.

        Args:
            dtos: Список DTO для создания реакций

        Returns:
            Количество успешно вставленных записей
        """
        if not dtos:
            return 0

        mappings = [
            {
                "chat_id": dto.chat_id,
                "user_id": dto.user_id,
                "message_id": dto.message_id,
                "action": dto.action,
                "emoji": dto.emoji,
                "message_url": dto.message_url,
                "created_at": dto.created_at,
            }
            for dto in dtos
        ]

        return await self._bulk_upsert_on_conflict_nothing(
            MessageReaction, mappings, "реакций"
        )
