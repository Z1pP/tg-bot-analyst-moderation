import logging
from typing import Any, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_chat_status import UserChatStatus
from repositories.base import BaseRepository, transactional

logger = logging.getLogger(__name__)


class UserChatStatusRepository(BaseRepository):
    async def _get_status(
        self,
        session: AsyncSession,
        user_id: int,
        chat_id: int,
    ) -> Optional[UserChatStatus]:
        """Выполняет запрос на получение статуса пользователя в чате."""
        result = await session.execute(
            select(UserChatStatus).where(
                and_(
                    UserChatStatus.user_id == user_id,
                    UserChatStatus.chat_id == chat_id,
                )
            )
        )
        return result.scalars().first()

    @transactional
    async def get_status(
        self,
        session: AsyncSession,
        /,
        user_id: int,
        chat_id: int,
    ) -> Optional[UserChatStatus]:
        status = await self._get_status(session, user_id, chat_id)

        if status:
            logger.info(
                "Получен статус для user_id=%s, chat_id=%s", user_id, chat_id
            )
        else:
            logger.info(
                "Статус для user_id=%s, chat_id=%s не найден", user_id, chat_id
            )
        return status

    @transactional
    async def get_or_create(
        self,
        session: AsyncSession,
        /,
        user_id: int,
        chat_id: int,
        defaults: Optional[dict[str, Any]] = None,
    ) -> tuple[UserChatStatus, bool]:
        """Получает или создает запись о статусе пользователя в чате."""
        status = await self._get_status(session, user_id, chat_id)

        if status:
            return status, False

        if defaults is None:
            defaults = {}

        create_params = {
            "user_id": user_id,
            "chat_id": chat_id,
            **defaults,
        }
        status = UserChatStatus(**create_params)
        session.add(status)
        await session.commit()
        await session.refresh(status)
        logger.info(
            "Создана новая запись UserChatStatus для user_id=%s, chat_id=%s",
            user_id,
            chat_id,
        )
        return status, True

    @transactional
    async def update_status(
        self,
        session: AsyncSession,
        /,
        user_id: int,
        chat_id: int,
        **kwargs: Any,
    ) -> Optional[UserChatStatus]:
        """Обновляет статус пользователя в чате."""
        status = await self._get_status(session, user_id, chat_id)

        if not status:
            logger.warning(
                "Статус для user_id=%s, chat_id=%s не найден для обновления",
                user_id,
                chat_id,
            )
            return None

        for key, value in kwargs.items():
            setattr(status, key, value)

        await session.commit()
        await session.refresh(status)
        logger.info(
            "Статус для user_id=%s, chat_id=%s обновлен", user_id, chat_id
        )
        return status
