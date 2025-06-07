import logging
from typing import Optional

from sqlalchemy import select

from database.session import async_session
from models.chat_session import ChatSession

logger = logging.getLogger(__name__)


class ChatRepository:
    async def get_chat(self, chat_id: str) -> Optional[ChatSession]:
        async with async_session() as session:
            try:
                return await session.scalar(
                    select(ChatSession).where(ChatSession.chat_id == chat_id)
                )
            except Exception as e:
                logger.error("Произошла ошибка при получении чата: %s, %s", chat_id, e)
                raise e

    async def get_all(self) -> list[ChatSession]:
        async with async_session() as session:
            try:
                result = await session.execute(select(ChatSession))
                return result.scalars().all()
            except Exception as e:
                logger.error("Произошла ошибка при получении всех чатов: %s", e)
                raise e

    async def create_chat(self, chat_id: str, title: str) -> ChatSession:
        async with async_session() as session:
            try:
                chat = ChatSession(
                    chat_id=chat_id,
                    title=title,
                )
                session.add(chat)
                await session.commit()
                await session.refresh(chat)
                return chat
            except Exception as e:
                logger.error("Произошла ошибка при создании чата: %s, %s", chat_id, e)
                await session.rollback()
                raise e
