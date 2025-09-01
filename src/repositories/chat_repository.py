import logging
from typing import List, Optional

from sqlalchemy import select

from database.session import async_session
from models.chat_session import ChatSession

logger = logging.getLogger(__name__)


class ChatRepository:
    async def get_chat(self, chat_id: int) -> Optional[ChatSession]:
        """Получает чат по идентификатору."""
        async with async_session() as session:
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

    async def get_chat_by_title(self, title: str) -> Optional[ChatSession]:
        """Получает чат по названию."""
        async with async_session() as session:
            try:
                chat = await session.scalar(
                    select(ChatSession).where(ChatSession.title == title)
                )
                if chat:
                    logger.info(
                        "Получен чат: chat_id=%s, title=%s", chat.chat_id, chat.title
                    )
                else:
                    logger.info("Чат не найден: title=%s", title)
                return chat
            except Exception as e:
                logger.error("Произошла ошибка при получении чата: %s, %s", title, e)
                raise e

    async def get_all(self) -> List[ChatSession]:
        """Получает список всех чатов."""
        async with async_session() as session:
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
        async with async_session() as session:
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
