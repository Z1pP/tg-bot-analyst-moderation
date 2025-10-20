import logging
from typing import Optional

from sqlalchemy import delete, select
from sqlalchemy.orm import joinedload

from database.session import DatabaseContextManager
from models import AdminChatAccess, ChatSession

logger = logging.getLogger(__name__)


class ChatTrackingRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

    async def add_chat_to_tracking(
        self,
        admin_id: int,
        chat_id: int,
        is_source: bool = True,
        is_target: bool = False,
    ) -> Optional[AdminChatAccess]:
        """Добавляет доступ к чату для администратора."""
        async with self._db.session() as session:
            try:
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
            except Exception as e:
                logger.error("Произошла ошибка при добавлении доступа к чату: %s", e)
                await session.rollback()
                raise e

    async def remove_chat_from_tracking(
        self,
        admin_id: int,
        chat_id: int,
    ) -> bool:
        """Удаляет доступ к чату для администратора."""
        async with self._db.session() as session:
            try:
                query = delete(AdminChatAccess).where(
                    AdminChatAccess.admin_id == admin_id,
                    AdminChatAccess.chat_id == chat_id,
                )
                result = await session.execute(query)
                await session.commit()

                if result.rowcount > 0:
                    logger.info(
                        "Удалено %d записей доступа к чату для администратора: admin_id=%s, chat_id=%s",
                        result.rowcount,
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
            except Exception as e:
                logger.error("Произошла ошибка при удалении доступа к чату: %s", e)
                await session.rollback()
                raise e

    async def get_access(
        self,
        admin_id: int,
        chat_id: int,
    ) -> Optional[AdminChatAccess]:
        """Проверяет наличие доступа администратора к чату."""
        async with self._db.session() as session:
            try:
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
            except Exception as e:
                logger.error("Произошла ошибка при проверке доступа к чату: %s", e)
                return None

    async def get_all_tracked_chats(self, admin_id: int) -> list[ChatSession]:
        """Получает все чаты администратора (и источники, и получатели)."""
        async with self._db.session() as session:
            try:
                query = (
                    select(ChatSession)
                    .join(AdminChatAccess, ChatSession.id == AdminChatAccess.chat_id)
                    .options(joinedload(ChatSession.admin_access))
                    .where(AdminChatAccess.admin_id == admin_id)
                    .order_by(ChatSession.title)
                    .distinct()
                )
                result = await session.execute(query)
                chats = result.unique().scalars().all()

                logger.info(
                    "Получено %d чатов для администратора: %s", len(chats), admin_id
                )
                return chats
            except Exception as e:
                logger.error(
                    "Произошла ошибка при получении всех чатов администратора: %s", e
                )
                return []
