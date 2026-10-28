import logging
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession

from dto.buffer import BufferedMessageReplyDTO
from models import ChatMessage, MessageReply
from repositories.base import BaseRepository, transactional

logger = logging.getLogger(__name__)


class MessageReplyRepository(BaseRepository):
    @transactional
    async def get_replies_by_period_date_for_users(
        self,
        session: AsyncSession,
        /,
        user_ids: list[int],
        start_date: datetime,
        end_date: datetime,
    ) -> list[MessageReply]:
        """
        Получает все ответы пользователей за указанный период.
        """
        if not user_ids:
            return []

        query = (
            select(MessageReply)
            .options(joinedload(MessageReply.chat_session))
            .where(
                MessageReply.reply_user_id.in_(user_ids),
                MessageReply.created_at.between(start_date, end_date),
            )
        )
        result = await session.execute(query)
        replies = list(result.scalars().all())
        logger.info(
            "Получено %d ответов для пользователей (%d) за период %s - %s",
            len(replies),
            len(user_ids),
            start_date,
            end_date,
        )
        return replies

    @transactional
    async def get_replies_by_chat_id_and_period(
        self,
        session: AsyncSession,
        /,
        chat_id: int,
        start_date: datetime,
        end_date: datetime,
        tracked_user_ids: Optional[list[int]] = None,
    ) -> list[MessageReply]:
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
        result = await session.execute(query)
        replies = list(result.scalars().all())
        logger.info(
            "Получено %d ответов для chat_id=%s за период %s - %s",
            len(replies),
            chat_id,
            start_date,
            end_date,
        )
        return replies

    @transactional
    async def get_replies_by_period_date_and_chats(
        self,
        session: AsyncSession,
        /,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
        chat_ids: list[int],
    ) -> list[MessageReply]:
        """Получает ответы пользователя в определенных чатах за период"""
        query = (
            select(MessageReply)
            .options(joinedload(MessageReply.chat_session))
            .where(
                MessageReply.reply_user_id == user_id,
                MessageReply.chat_id.in_(chat_ids),
                MessageReply.created_at.between(start_date, end_date),
            )
        )
        result = await session.execute(query)
        return list(result.scalars().all())

    @transactional
    async def bulk_create_replies(
        self, session: AsyncSession, /, dtos: List[BufferedMessageReplyDTO]
    ) -> tuple[int, List[BufferedMessageReplyDTO]]:
        """
        Массовое создание reply сообщений с защитой от дубликатов.

        Args:
            dtos: Список DTO для создания reply сообщений

        Returns:
            Кортеж (количество успешно вставленных записей, список DTO без родителя)
        """
        if not dtos:
            return (0, [])

        # Собираем уникальные пары (chat_id, message_id_str) для поиска
        message_lookup: dict[tuple[int, str], list[Any] | int | None] = {}
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
            message = result.scalars().first()
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
        mappings: List[dict[str, Any]] = []
        failed_dtos: List[BufferedMessageReplyDTO] = []
        for dto in dtos:
            db_message_id = message_lookup.get(
                (dto.chat_id, dto.reply_message_id_str)
            )
            if db_message_id is None:
                failed_dtos.append(dto)
                continue

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
            return (0, failed_dtos)

        inserted_count = await self._bulk_upsert_on_conflict_nothing(
            MessageReply, mappings, "reply сообщений"
        )
        return (inserted_count, failed_dtos)
