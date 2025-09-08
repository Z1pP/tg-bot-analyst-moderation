import logging
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.session import async_session
from dto.message_reply import CreateMessageReplyDTO
from models import MessageReply

logger = logging.getLogger(__name__)


class MessageReplyRepository:
    async def get_replies_by_period_date(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> list[MessageReply]:
        """
        Получает все ответы пользователя за указанный период.
        """
        async with async_session() as session:
            query = (
                select(MessageReply)
                .options(joinedload(MessageReply.chat_session))
                .where(
                    MessageReply.reply_user_id == user_id,
                    MessageReply.created_at.between(start_date, end_date),
                )
            )
            try:
                result = await session.execute(query)
                replies = result.scalars().all()
                logger.info(
                    "Получено %d ответов для user_id=%s за период %s - %s",
                    len(replies),
                    user_id,
                    start_date,
                    end_date,
                )
                return replies
            except Exception as e:
                logger.error(
                    "Ошибка при получении ответов по периоду: user_id=%s, период=%s-%s, %s",
                    user_id,
                    start_date,
                    end_date,
                    e,
                )
                return []

    async def create_reply_message(self, dto: CreateMessageReplyDTO) -> MessageReply:
        async with async_session() as session:
            try:
                new_reply = MessageReply(
                    chat_id=dto.chat_id,
                    original_message_url=dto.original_message_url,
                    reply_message_id=dto.reply_message_id,
                    reply_user_id=dto.reply_user_id,
                    response_time_seconds=dto.response_time_seconds,
                )
                session.add(new_reply)
                await session.commit()
                await session.refresh(new_reply)
                logger.info(
                    "Создан новый ответ: chat_id=%s, reply_user_id=%s, response_time=%s сек.",
                    dto.chat_id,
                    dto.reply_user_id,
                    dto.response_time_seconds,
                )
                return new_reply
            except Exception as e:
                logger.error("Ошибка при создании ответа: %s", e)
                await session.rollback()
                raise e

    async def get_replies_by_chat_id_and_period(
        self,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
        tracked_user_ids: list[int] = None,
    ) -> list[MessageReply]:
        async with async_session() as session:
            query = (
                select(MessageReply)
                .options(joinedload(MessageReply.chat_session))
                .where(
                    MessageReply.chat_id == chat_id,
                    MessageReply.created_at.between(start_date, end_date),
                )
            )
            # Фильтруем только по отслеживаемым пользователям
            if tracked_user_ids:
                query = query.where(MessageReply.reply_user_id.in_(tracked_user_ids))
            try:
                result = await session.execute(query)
                replies = result.scalars().all()
                logger.info(
                    "Получено %d ответов для chat_id=%s за период %s - %s",
                    len(replies),
                    chat_id,
                    start_date,
                    end_date,
                )
                return replies
            except Exception as e:
                logger.error(
                    "Ошибка при получении ответов по chat_id: chat_id=%s, период=%s-%s, %s",
                    chat_id,
                    start_date,
                    end_date,
                    e,
                )
                return []

    async def get_replies_by_period_date_and_chats(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        chat_ids: list[int],
    ) -> list[MessageReply]:
        """Получает ответы пользователя в определенных чатах за период"""
        async with async_session() as session:
            query = (
                select(MessageReply)
                .options(joinedload(MessageReply.chat_session))
                .where(
                    MessageReply.reply_user_id == user_id,
                    MessageReply.chat_id.in_(chat_ids),
                    MessageReply.created_at.between(start_date, end_date),
                )
            )
            try:
                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                logger.error(f"Error getting replies by chats: {e}")
                return []
