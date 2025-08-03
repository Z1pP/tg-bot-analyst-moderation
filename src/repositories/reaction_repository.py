import logging
from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.session import async_session
from dto.reaction import MessageReactionDTO
from models import MessageReaction

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
