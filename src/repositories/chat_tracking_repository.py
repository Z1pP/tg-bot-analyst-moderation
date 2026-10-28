import logging
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload, selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from models import AdminChatAccess, ChatSession
from repositories.base import BaseRepository, transactional

logger = logging.getLogger(__name__)


class ChatTrackingRepository(BaseRepository):
    @transactional
    async def add_chat_to_tracking(
        self,
        session: AsyncSession,
        /,
        admin_id: int,
        chat_id: int,
        is_source: bool = True,
        is_target: bool = False,
    ) -> Optional[AdminChatAccess]:
        """Добавляет доступ к чату для администратора."""
        chat_access = AdminChatAccess(
            admin_id=admin_id,
            chat_id=chat_id,
            is_source=is_source,
            is_target=is_target,
        )
        session.add(chat_access)
        await session.commit()
        await session.refresh(chat_access)
        logger.info(
            "Добавлен чат для отслеживания администратором: admin_id=%s, chat_id=%s",
            admin_id,
            chat_id,
        )
        return chat_access

    @transactional
    async def remove_chat_from_tracking(
        self,
        session: AsyncSession,
        /,
        admin_id: int,
        chat_id: int,
    ) -> bool:
        """Удаляет доступ к чату для администратора."""
        query = delete(AdminChatAccess).where(
            AdminChatAccess.admin_id == admin_id,
            AdminChatAccess.chat_id == chat_id,
        )
        result = await session.execute(query)
        await session.commit()

        rowcount: int = getattr(result, "rowcount", 0) or 0
        if rowcount > 0:
            logger.info(
                "Удалено %d записей доступа к чату для администратора: admin_id=%s, chat_id=%s",
                rowcount,
                admin_id,
                chat_id,
            )
            return True
        else:
            logger.warning(
                "Доступ к чату не найден для администратора: admin_id=%s, chat_id=%s",
                admin_id,
                chat_id,
            )
            return False

    @transactional
    async def get_access(
        self,
        session: AsyncSession,
        /,
        admin_id: int,
        chat_id: int,
    ) -> Optional[AdminChatAccess]:
        """Проверяет наличие доступа администратора к чату."""
        query = select(AdminChatAccess).where(
            AdminChatAccess.admin_id == admin_id,
            AdminChatAccess.chat_id == chat_id,
        )
        result = await session.execute(query)
        access = result.scalars().first()

        if access:
            logger.info(
                "Найден доступ администратора к чату: admin_id=%s, chat_id=%s",
                admin_id,
                chat_id,
            )
        else:
            logger.info(
                "Доступ администратора к чату не найден: admin_id=%s, chat_id=%s",
                admin_id,
                chat_id,
            )

        return access

    @transactional
    async def get_all_tracked_chats(self, session: AsyncSession, /, admin_id: int) -> list[ChatSession]:
        """Получает все чаты администратора (и источники, и получатели)."""
        query = (
            select(ChatSession)
            .join(AdminChatAccess, ChatSession.id == AdminChatAccess.chat_id)
            .options(
                joinedload(ChatSession.admin_access),
                selectinload(ChatSession.settings),
            )
            .where(AdminChatAccess.admin_id == admin_id)
            .order_by(ChatSession.title)
            .distinct()
        )
        result = await session.execute(query)
        chats = result.unique().scalars().all()

        # Предварительно обращаемся к свойствам, чтобы они точно были в памяти
        for chat in chats:
            _ = chat.settings
            _ = chat.admin_access

        # Отсоединяем всё разом. Это безопаснее, чем expunge по одному.
        session.expunge_all()

        logger.info(
            "Получено %d чатов для администратора: %s", len(chats), admin_id
        )
        return list(chats)

    @transactional
    async def delete_all_tracked_chats_for_admin(self, session: AsyncSession, /, admin_id: int) -> int:
        """Удаляет все отслеживаемые чаты для админа."""
        query = delete(AdminChatAccess).where(
            AdminChatAccess.admin_id == admin_id
        )
        result = await session.execute(query)
        await session.commit()
        rowcount: int = getattr(result, "rowcount", 0) or 0
        logger.info(
            "Удалено %d отслеживаемых чатов для администратора: admin_id=%s",
            rowcount,
            admin_id,
        )
        return rowcount
