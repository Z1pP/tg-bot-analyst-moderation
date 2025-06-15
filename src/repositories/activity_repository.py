import logging
from datetime import datetime
from typing import List, Optional

from sqlalchemy import select

from database.session import async_session
from dto.activity import CreateActivityDTO
from models import MessageReply, ModeratorActivity

logger = logging.getLogger(__name__)


class ActivityRepository:
    async def create_activity(self, dto: CreateActivityDTO) -> ModeratorActivity:
        """Создает запись об активности модератора."""
        new_activity = ModeratorActivity(
            user_id=dto.user_id,
            chat_id=dto.chat_id,
            last_message_id=dto.last_message_id,
            next_message_id=dto.next_message_id,
            inactive_period_seconds=dto.inactive_period_seconds,
        )
        async with async_session() as session:
            try:
                session.add(new_activity)
                await session.commit()
                await session.refresh(new_activity)
                logger.info(
                    "Создана новая активность: user_id=%s, chat_id=%s, inactive_period=%s сек.",
                    dto.user_id,
                    dto.chat_id,
                    dto.inactive_period_seconds,
                )
                return new_activity
            except Exception as e:
                logger.error(
                    "Ошибка при создании активности: user_id=%s, chat_id=%s, %s",
                    dto.user_id,
                    dto.chat_id,
                    e,
                )
                await session.rollback()
                raise e

    async def create_reply_activity(
        self, message: MessageReply, activity: ModeratorActivity
    ) -> ModeratorActivity:
        """Создает запись об активности на основе ответа модератора."""
        new_activity = ModeratorActivity(
            user_id=message.reply_user_id,
            chat_id=message.chat_id,
            message_id=message.id,
        )
        async with async_session() as session:
            try:
                session.add(new_activity)
                await session.commit()
                await session.refresh(new_activity)
                logger.info(
                    "Создана активность по ответу: user_id=%s, chat_id=%s, message_id=%s",
                    message.reply_user_id,
                    message.chat_id,
                    message.id,
                )
                return activity
            except Exception as e:
                logger.error(
                    "Ошибка при создании активности по ответу: user_id=%s, chat_id=%s, %s",
                    message.reply_user_id,
                    message.chat_id,
                    e,
                )
                await session.rollback()
                raise e

    async def get_last_activity(
        self, user_id: int, chat_id: int
    ) -> Optional[ModeratorActivity]:
        """Получает последнюю активность модератора в чате."""
        async with async_session() as session:
            try:
                query = (
                    select(ModeratorActivity)
                    .where(
                        ModeratorActivity.user_id == user_id,
                        ModeratorActivity.chat_id == chat_id,
                    )
                    .order_by(ModeratorActivity.created_at.desc())
                )
                result = await session.execute(query)
                activity = result.scalars().first()

                if activity:
                    logger.info(
                        "Получена последняя активность: user_id=%s, chat_id=%s, created_at=%s",
                        user_id,
                        chat_id,
                        activity.created_at,
                    )
                else:
                    logger.info(
                        "Активность не найдена: user_id=%s, chat_id=%s",
                        user_id,
                        chat_id,
                    )

                return activity
            except Exception as e:
                logger.error(
                    "Ошибка при получении последней активности: user_id=%s, chat_id=%s, %s",
                    user_id,
                    chat_id,
                    e,
                )
                return None

    async def get_activities_by_period_date(
        self, start_date: datetime, end_date: datetime
    ) -> List[ModeratorActivity]:
        """Получает активности за указанный период."""
        async with async_session() as session:
            try:
                query = (
                    select(ModeratorActivity)
                    .where(
                        ModeratorActivity.created_at >= start_date,
                        ModeratorActivity.created_at <= end_date,
                    )
                    .order_by(ModeratorActivity.created_at.desc())
                )
                result = await session.execute(query)
                activities = result.scalars().all()

                logger.info(
                    "Получено %d активностей за период %s - %s",
                    len(activities),
                    start_date,
                    end_date,
                )
                return activities
            except Exception as e:
                logger.error(
                    "Ошибка при получении активностей за период %s - %s: %s",
                    start_date,
                    end_date,
                    e,
                )
                return []
