import logging
from datetime import datetime
from typing import List

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from database.session import async_session
from dto.daily_activity import PopularReactionDTO, UserReactionActivityDTO
from dto.reaction import MessageReactionDTO
from models import MessageReaction, User

logger = logging.getLogger(__name__)


class MessageReactionRepository:
    async def add_reaction(self, dto: MessageReactionDTO) -> MessageReaction:
        async with async_session() as session:
            try:
                logger.info(
                    f"Создание реакции: пользователь {dto.user_id}, сообщение {dto.message_id}, эмодзи {dto.emoji}"
                )

                reaction = MessageReaction(
                    chat_id=dto.chat_id,
                    user_id=dto.user_id,
                    message_id=dto.message_id,
                    action=dto.action,
                    emoji=dto.emoji,
                    message_url=dto.message_url,
                )
                session.add(reaction)
                await session.commit()
                await session.refresh(reaction)

                logger.info(f"Реакция успешно создана с ID: {reaction.id}")
                return reaction
            except Exception as e:
                logger.error(f"Ошибка при создании реакции: {str(e)}")
                await session.rollback()
                raise e

    async def get_reactions_by_chat_and_period(
        self,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[MessageReaction]:
        async with async_session() as session:
            try:
                logger.debug(f"Получение реакций для чата с ID={chat_id}")

                query = (
                    select(MessageReaction)
                    .options(joinedload(MessageReaction.user))
                    .where(
                        MessageReaction.chat_id == chat_id,
                        MessageReaction.created_at.between(start_date, end_date),
                    )
                )
                result = await session.execute(query)
                reactions = result.scalars().all()

                logger.info(f"Найдено {len(reactions)} реакций для чата с ID={chat_id}")
                return reactions
            except Exception as e:
                logger.error(
                    f"Ошибка при получении реакций для чата с ID={chat_id}: {str(e)}"
                )
                raise e

    async def get_reactions_by_user_and_period(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> List[MessageReaction]:
        async with async_session() as session:
            try:
                logger.debug(f"Получение реакций для пользователя с ID={user_id}")

                query = (
                    select(MessageReaction)
                    .options(joinedload(MessageReaction.user))
                    .where(
                        MessageReaction.user_id == user_id,
                        MessageReaction.created_at.between(start_date, end_date),
                    )
                )
                result = await session.execute(query)
                reactions = result.scalars().all()

                logger.info(
                    f"Найдено {len(reactions)} реакций для пользователя {user_id}"
                )
                return reactions
            except Exception as e:
                logger.error(
                    f"Ошибка при получении реакций для пользователя {user_id}: {str(e)}"
                )
                raise e

    async def get_daily_top_reactors(
        self, chat_id: int, date: datetime, limit: int = 10
    ) -> List[UserReactionActivityDTO]:
        """
        Получает топ пользователей по количеству реакций за день.
        """
        async with async_session() as session:
            try:
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = date.replace(
                    hour=23, minute=59, second=59, microsecond=999999
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
                    f"Получен топ-{len(top_reactors)} по реакциям для chat_id={chat_id} за {date.strftime('%Y-%m-%d')}"
                )
                return top_reactors

            except Exception as e:
                logger.error(
                    f"Ошибка при получении топа по реакциям: chat_id={chat_id}, дата={date.strftime('%Y-%m-%d')}, {e}"
                )
                return []

    async def get_daily_popular_reactions(
        self, chat_id: int, date: datetime, limit: int = 3
    ) -> List[PopularReactionDTO]:
        """
        Получает самые популярные реакции за день.
        """
        async with async_session() as session:
            try:
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = date.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )

                query = (
                    select(
                        MessageReaction.emoji,
                        func.count(MessageReaction.id).label("count"),
                    )
                    .where(
                        MessageReaction.chat_id == chat_id,
                        MessageReaction.created_at.between(start_date, end_date),
                    )
                    .group_by(MessageReaction.emoji)
                    .order_by(func.count(MessageReaction.id).desc())
                    .limit(limit)
                )

                result = await session.execute(query)
                rows = result.fetchall()

                popular_reactions = []
                for rank, row in enumerate(rows, 1):
                    popular_reactions.append(
                        PopularReactionDTO(emoji=row.emoji, count=row.count, rank=rank)
                    )

                logger.info(
                    f"Получено {len(popular_reactions)} популярных реакций для chat_id={chat_id} за {date.strftime('%Y-%m-%d')}"
                )
                return popular_reactions

            except Exception as e:
                logger.error(
                    f"Ошибка при получении популярных реакций: chat_id={chat_id}, дата={date.strftime('%Y-%m-%d')}, {e}"
                )
                return []

    async def get_reactions_by_user_and_period_and_chats(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        chat_ids: List[int],
    ) -> List[MessageReaction]:
        """Получает реакции пользователя в определенных чатах за период"""
        async with async_session() as session:
            try:
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
                return result.scalars().all()
            except Exception as e:
                logger.error(f"Error getting reactions by chats: {e}")
                return []
