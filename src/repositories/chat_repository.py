import logging
from typing import List, Optional

from sqlalchemy import select

from database.session import DatabaseContextManager
from models.chat_session import ChatSession

logger = logging.getLogger(__name__)


class ChatRepository:
    def __init__(self, db_manager: DatabaseContextManager) -> None:
        self._db = db_manager

    async def get_chat(self, chat_id: int) -> Optional[ChatSession]:
        """Получает чат по идентификатору."""
        async with self._db.session() as session:
            try:
                chat = await session.get(ChatSession, chat_id)
                if chat:
                    logger.info(
                        "Получен чат: chat_id=%s, title=%s", chat_id, chat.title
                    )
                else:
                    logger.info("Чат не найден: chat_id=%s", chat_id)
                return chat
            except Exception as e:
                logger.error("Произошла ошибка при получении чата: %s, %s", chat_id, e)
                raise e

    async def get_chat_by_chat_id(self, chat_tgid: str) -> Optional[ChatSession]:
        """Получает чат по Telegram chat_id."""
        async with self._db.session() as session:
            try:
                chat = await session.scalar(
                    select(ChatSession).where(ChatSession.chat_id == chat_tgid)
                )
                if chat:
                    logger.info(
                        "Получен чат: chat_id=%s, title=%s", chat.chat_id, chat.title
                    )
                else:
                    logger.info("Чат не найден: chat_id=%s", chat_tgid)
                return chat
            except Exception as e:
                logger.error(
                    "Произошла ошибка при получении чата: %s, %s", chat_tgid, e
                )
                raise e

    async def get_all(self) -> List[ChatSession]:
        """Получает список всех чатов."""
        async with self._db.session() as session:
            try:
                result = await session.execute(select(ChatSession))
                chats = result.scalars().all()
                logger.info("Получено %d чатов", len(chats))
                return chats
            except Exception as e:
                logger.error("Произошла ошибка при получении всех чатов: %s", e)
                raise e

    async def create_chat(self, chat_id: str, title: str) -> ChatSession:
        """Создает новый чат."""
        async with self._db.session() as session:
            try:
                chat = ChatSession(
                    chat_id=chat_id,
                    title=title,
                )
                session.add(chat)
                await session.commit()
                await session.refresh(chat)
                logger.info("Создан новый чат: chat_id=%s, title=%s", chat_id, title)
                return chat
            except Exception as e:
                logger.error("Произошла ошибка при создании чата: %s, %s", chat_id, e)
                await session.rollback()
                raise e

    async def update_chat(self, chat_id: int, title: str) -> ChatSession:
        """Обновляет название чата."""
        async with self._db.session() as session:
            try:
                chat = await session.get(ChatSession, chat_id)
                if chat:
                    chat.title = title
                    await session.commit()
                    await session.refresh(chat)
                    logger.info(
                        "Обновлен чат: chat_id=%s, new_title=%s", chat_id, title
                    )
                    return chat
                else:
                    logger.error("Чат не найден для обновления: chat_id=%s", chat_id)
                    raise ValueError(f"Чат с id {chat_id} не найден")
            except Exception as e:
                logger.error("Произошла ошибка при обновлении чата: %s, %s", chat_id, e)
                await session.rollback()
                raise e

    async def get_tracked_chats_for_admin(self, admin_tg_id: int) -> List[ChatSession]:
        """Получает отслеживаемые чаты для администратора"""
        async with self._db.session() as session:
            try:
                # Предполагаем, что все чаты отслеживаются для всех админов
                # В реальности здесь должна быть связь admin -> tracked_chats
                result = await session.execute(select(ChatSession))
                chats = result.scalars().all()
                logger.info(
                    f"Получено {len(chats)} отслеживаемых чатов для admin {admin_tg_id}"
                )
                return chats
            except Exception as e:
                logger.error(
                    f"Error getting tracked chats for admin {admin_tg_id}: {e}"
                )
                return []

    async def get_archive_chats(
        self,
        source_chat_tgid: str,
    ) -> Optional[List[ChatSession]]:
        """Получает архивный чат по названию источника"""
        async with self._db.session() as session:
            try:
                query = select(ChatSession).where(
                    ChatSession.archive_chat_id == source_chat_tgid
                )

                result = await session.execute(query)
                chats = result.scalars().all()

                logger.info("Получено %d архивных чатов", len(chats))
                return chats
            except Exception as e:
                logger.error("Произошла ошибка при получении архивных чатов: %s", e)
                raise e
