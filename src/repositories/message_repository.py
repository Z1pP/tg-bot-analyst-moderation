import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.session import async_session
from dto.message import CreateMessageDTO
from models import ChatMessage

logger = logging.getLogger(__name__)


class MessageRepository:
    async def get_last_user_message(
        self, user_id: int, chat_id: int
    ) -> Optional[ChatMessage]:
        async with async_session() as session:
            try:
                return await session.scalar(
                    select(ChatMessage)
                    .where(
                        ChatMessage.user_id == user_id,
                        ChatMessage.chat_id == chat_id,
                    )
                    .order_by(ChatMessage.id.desc())
                    .limit(1)
                    .offset(1)
                )
            except Exception as e:
                logger.error("Ошибка при получении последнего сообщения: %s", e)
                return None

    async def create_new_message(self, dto: CreateMessageDTO) -> ChatMessage:
        async with async_session() as session:
            try:
                new_message = ChatMessage(
                    user_id=dto.user_id,
                    chat_id=dto.chat_id,
                    message_id=dto.message_id,
                    message_type=dto.message_type,
                    content_type=dto.content_type,
                    text=dto.text,
                )
                session.add(new_message)
                await session.commit()
                await session.refresh(new_message)
                logger.info(
                    "Создано новое сообщение: user_id=%s, chat_id=%s, message_id=%s",
                    dto.user_id,
                    dto.chat_id,
                    dto.message_id,
                )
                return new_message
            except Exception as e:
                logger.error("Ошибка при создании сообщения: %s", e)
                await session.rollback()
                raise e

    async def get_messages_by_period_date(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> list[ChatMessage]:
        async with async_session() as session:
            query = (
                select(ChatMessage)
                .options(joinedload(ChatMessage.chat_session))
                .where(
                    ChatMessage.user_id == user_id,
                    ChatMessage.created_at.between(start_date, end_date),
                )
            )
            try:
                result = await session.execute(query)
                messages = result.scalars().all()
                logger.info(
                    "Получено %d сообщений для user_id=%s за период %s - %s",
                    len(messages),
                    user_id,
                    start_date,
                    end_date,
                )
                return messages
            except Exception as e:
                logger.error(
                    "Ошибка при получении сообщений по периоду: user_id=%s, период=%s-%s, %s",
                    user_id,
                    start_date,
                    end_date,
                    e,
                )
                return []

    async def get_messages_by_chat_id_and_period(
        self, chat_id: int, start_date: datetime, end_date: datetime
    ) -> list[ChatMessage]:
        """
        Получает сообщения из чата за период времени.
        """
        async with async_session() as session:
            query = (
                select(ChatMessage)
                .options(joinedload(ChatMessage.chat_session))
                .where(
                    ChatMessage.chat_id == chat_id,
                    ChatMessage.created_at.between(start_date, end_date),
                )
            )
            try:
                result = await session.execute(query)
                messages = result.scalars().all()
                logger.info(
                    "Получено %d сообщений для chat_id=%s за период %s - %s",
                    len(messages),
                    chat_id,
                    start_date,
                    end_date,
                )
                return messages
            except Exception as e:
                logger.error(
                    "Ошибка при получении сообщений по chat_id: chat_id=%s, период=%s-%s, %s",
                    chat_id,
                    start_date,
                    end_date,
                    e,
                )
                return []
