import logging
from datetime import datetime
from typing import List

from sqlalchemy import func, select
from sqlalchemy.orm import joinedload

from dto.buffer import BufferedMessageDTO
from dto.daily_activity import UserDailyActivityDTO
from models import ChatMessage, User
from repositories.base import BaseRepository
from utils.date_utils import validate_and_normalize_period

logger = logging.getLogger(__name__)


class MessageRepository(BaseRepository):
    async def get_messages_for_summary(
        self,
        chat_id: int,
        limit: int,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ):
        """
        Выбирает только текст и имя пользователя.
        Игнорирует системные сообщения и медиа.
        """
        async with self._db.session() as session:
            query = (
                select(
                    ChatMessage.text,
                    User.username,
                )
                .join(User, ChatMessage.user_id == User.id)
                .where(
                    ChatMessage.chat_id == chat_id,
                    ChatMessage.content_type == "text",
                    ChatMessage.text.is_not(None),
                )
            )

            if start_date and end_date:
                query = query.where(
                    ChatMessage.created_at.between(start_date, end_date)
                )

            query = query.order_by(ChatMessage.created_at.desc()).limit(limit)

            result = await session.execute(query)
            # Возвращаем список кортежей (text, username) в хронологическом порядке
            return list(reversed(result.all()))

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

    async def get_messages_by_period_date_for_users(
        self,
        user_ids: list[int],
        start_date: datetime,
        end_date: datetime,
    ) -> list[ChatMessage]:
        """Получает сообщения для списка пользователей за период."""
        if not user_ids:
            return []

        async with self._db.session() as session:
            query = (
                select(ChatMessage)
                .options(joinedload(ChatMessage.chat_session))
                .where(
                    ChatMessage.user_id.in_(user_ids),
                    ChatMessage.created_at.between(start_date, end_date),
                )
            )
            try:
                result = await session.execute(query)
                messages = result.scalars().all()
                logger.info(
                    "Получено %d сообщений для пользователей (%d) за период %s - %s",
                    len(messages),
                    len(user_ids),
                    start_date,
                    end_date,
                )
                return messages
            except Exception as e:
                logger.error(
                    "Ошибка при получении сообщений по периоду для пользователей: users=%s, период=%s-%s, %s",
                    user_ids,
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
        self,
        chat_id: int,
        date: datetime | None = None,
        limit: int = 10,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
    ) -> List[UserDailyActivityDTO]:
        """
        Получает топ активных пользователей за период в чате.
        """
        async with self._db.session() as session:
            try:
                start_date, end_date = validate_and_normalize_period(
                    date, start_date, end_date
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
                    "Получен топ-%d пользователей для chat_id=%s за период %s - %s",
                    len(top_users),
                    chat_id,
                    start_date.strftime("%Y-%m-%d"),
                    end_date.strftime("%Y-%m-%d"),
                )
                return top_users

            except Exception as e:
                logger.error(
                    "Ошибка при получении топа пользователей: chat_id=%s, период=%s-%s, %s",
                    chat_id,
                    start_date.strftime("%Y-%m-%d") if start_date else "None",
                    end_date.strftime("%Y-%m-%d") if end_date else "None",
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

    async def bulk_create_messages(self, dtos: List[BufferedMessageDTO]) -> int:
        """
        Массовое создание сообщений с защитой от дубликатов.

        Args:
            dtos: Список DTO для создания сообщений

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
                "message_type": dto.message_type,
                "content_type": dto.content_type,
                "text": dto.text,
                "created_at": dto.created_at,
            }
            for dto in dtos
        ]

        return await self._bulk_upsert_on_conflict_nothing(
            ChatMessage, mappings, "сообщений"
        )

    async def get_max_message_id(self, chat_id: int) -> int | None:
        """Возвращает максимальный ID сообщения в чате."""
        async with self._db.session() as session:
            query = select(func.max(ChatMessage.id)).where(
                ChatMessage.chat_id == chat_id
            )
            result = await session.execute(query)
            return result.scalar()

    async def count_messages_since(self, chat_id: int, last_id: int) -> int:
        """Считает количество новых текстовых сообщений после указанного ID."""
        async with self._db.session() as session:
            query = select(func.count(ChatMessage.id)).where(
                ChatMessage.chat_id == chat_id,
                ChatMessage.id > last_id,
                ChatMessage.content_type == "text",
                ChatMessage.text.is_not(None),
            )
            result = await session.execute(query)
            return result.scalar() or 0
