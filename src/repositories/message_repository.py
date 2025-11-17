import logging
from datetime import datetime
from typing import List

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from database.session import DatabaseContextManager
from dto.daily_activity import UserDailyActivityDTO
from dto.message import CreateMessageDTO
from models import ChatMessage, User

logger = logging.getLogger(__name__)


class MessageRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

    async def create_new_message(self, dto: CreateMessageDTO) -> ChatMessage:
        async with self._db.session() as session:
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
        async with self._db.session() as session:
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
        self,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
        tracked_user_ids: list[int] = None,
    ) -> list[ChatMessage]:
        """
        Получает сообщения из чата за период времени для отслеживаемых пользователей.
        """
        async with self._db.session() as session:
            query = (
                select(ChatMessage)
                .options(
                    joinedload(ChatMessage.chat_session), joinedload(ChatMessage.user)
                )
                .where(
                    ChatMessage.chat_id == chat_id,
                    ChatMessage.created_at.between(start_date, end_date),
                )
            )

            # Фильтруем только по отслеживаемым пользователям
            if tracked_user_ids:
                query = query.where(ChatMessage.user_id.in_(tracked_user_ids))
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

    async def get_daily_top_users(
        self, chat_id: int, date: datetime, limit: int = 10
    ) -> List[UserDailyActivityDTO]:
        """
        Получает топ активных пользователей за день в чате.
        """
        async with self._db.session() as session:
            try:
                start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
                end_date = date.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )

                query = (
                    select(
                        ChatMessage.user_id,
                        User.username,
                        func.count(ChatMessage.id).label("message_count"),
                    )
                    .join(User, ChatMessage.user_id == User.id, isouter=True)
                    .where(
                        ChatMessage.chat_id == chat_id,
                        ChatMessage.created_at.between(start_date, end_date),
                    )
                    .group_by(ChatMessage.user_id, User.username)
                    .order_by(func.count(ChatMessage.id).desc())
                    .limit(limit)
                )

                result = await session.execute(query)
                rows = result.fetchall()

                top_users = []
                for rank, row in enumerate(rows, 1):
                    top_users.append(
                        UserDailyActivityDTO(
                            user_id=row.user_id,
                            username=row.username or f"User ID: {row.user_id}",
                            message_count=row.message_count,
                            rank=rank,
                        )
                    )

                logger.info(
                    "Получен топ-%d пользователей для chat_id=%s за %s",
                    len(top_users),
                    chat_id,
                    date.strftime("%Y-%m-%d"),
                )
                return top_users

            except Exception as e:
                logger.error(
                    "Ошибка при получении топа пользователей: chat_id=%s, дата=%s, %s",
                    chat_id,
                    date.strftime("%Y-%m-%d"),
                    e,
                )
                return []

    async def get_messages_by_period_date_and_chats(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        chat_ids: List[int],
    ) -> List[ChatMessage]:
        """Получает сообщения пользователя в определенных чатах за период"""
        async with self._db.session() as session:
            query = (
                select(ChatMessage)
                .options(joinedload(ChatMessage.chat_session))
                .where(
                    ChatMessage.user_id == user_id,
                    ChatMessage.chat_id.in_(chat_ids),
                    ChatMessage.created_at.between(start_date, end_date),
                )
            )
            try:
                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                logger.error(f"Error getting messages by chats: {e}")
                return []
