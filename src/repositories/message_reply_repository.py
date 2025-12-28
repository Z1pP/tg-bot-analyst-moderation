import logging
from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import joinedload

from database.session import DatabaseContextManager
from dto.buffer import BufferedMessageReplyDTO
from models import ChatMessage, MessageReply

logger = logging.getLogger(__name__)


class MessageReplyRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

    async def get_replies_by_period_date(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> list[MessageReply]:
        """
        Получает все ответы пользователя за указанный период.
        """
        async with self._db.session() as session:
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

    async def get_replies_by_chat_id_and_period(
        self,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
        tracked_user_ids: list[int] = None,
    ) -> list[MessageReply]:
        async with self._db.session() as session:
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
        async with self._db.session() as session:
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

    async def bulk_create_replies(self, dtos: List[BufferedMessageReplyDTO]) -> int:
        """
        Массовое создание reply сообщений с защитой от дубликатов.

        Args:
            dtos: Список DTO для создания reply сообщений

        Returns:
            Количество успешно вставленных записей
        """
        if not dtos:
            return 0

        async with self._db.session() as session:
            try:
                # Собираем уникальные пары (chat_id, message_id_str) для поиска
                message_lookup = {}
                for dto in dtos:
                    key = (dto.chat_id, dto.reply_message_id_str)
                    if key not in message_lookup:
                        message_lookup[key] = []

                # Ищем ChatMessage по message_id и chat_id для получения DB id
                for (chat_id, message_id_str), _ in message_lookup.items():
                    query = select(ChatMessage).where(
                        ChatMessage.chat_id == chat_id,
                        ChatMessage.message_id == message_id_str,
                    )
                    result = await session.execute(query)
                    message = result.scalar_one_or_none()
                    if message:
                        message_lookup[(chat_id, message_id_str)] = message.id
                    else:
                        # Сообщение еще не обработано воркером, пропускаем этот reply
                        logger.warning(
                            "ChatMessage не найден для reply: chat_id=%s, message_id=%s",
                            chat_id,
                            message_id_str,
                        )
                        message_lookup[(chat_id, message_id_str)] = None

                # Подготавливаем данные для bulk insert, пропуская те, где не найден ChatMessage
                mappings = []
                for dto in dtos:
                    db_message_id = message_lookup.get(
                        (dto.chat_id, dto.reply_message_id_str)
                    )
                    if db_message_id is None:
                        continue  # Пропускаем, если сообщение еще не обработано

                    mappings.append(
                        {
                            "chat_id": dto.chat_id,
                            "original_message_url": dto.original_message_url,
                            "reply_message_id": db_message_id,
                            "reply_user_id": dto.reply_user_id,
                            "response_time_seconds": dto.response_time_seconds,
                            "created_at": dto.created_at,
                        }
                    )

                if not mappings:
                    logger.warning(
                        "Нет валидных reply для вставки (все сообщения еще не обработаны)"
                    )
                    return 0

                # Используем PostgreSQL INSERT ... ON CONFLICT DO NOTHING
                stmt = (
                    insert(MessageReply.__table__)
                    .values(mappings)
                    .on_conflict_do_nothing()
                )

                result = await session.execute(stmt)
                await session.commit()

                inserted_count = (
                    result.rowcount if hasattr(result, "rowcount") else len(mappings)
                )

                logger.info(
                    "Массово создано reply сообщений: %d из %d (пропущено %d из-за отсутствия ChatMessage)",
                    inserted_count,
                    len(mappings),
                    len(dtos) - len(mappings),
                )
                return inserted_count
            except Exception as e:
                logger.error(
                    "Ошибка при массовом создании reply сообщений: %s", e, exc_info=True
                )
                await session.rollback()
                return 0
