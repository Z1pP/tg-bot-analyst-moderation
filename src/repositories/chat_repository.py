from datetime import datetime
from typing import Optional

from sqlalchemy import select

from database.session import async_session
from models.chat_session import ChatSession


class ChatRepository:
    async def get_chat(self, chat_id: str) -> Optional[ChatSession]:
        async with async_session() as session:
            try:
                return await session.scalar(
                    select(ChatSession).where(ChatSession.chat_id == chat_id)
                )
            except Exception as e:
                print(str(e))
                return None

    async def create_chat(self, chat_id: str, title: str) -> ChatSession:
        async with async_session() as session:
            try:
                chat = ChatSession(
                    chat_id=chat_id,
                    title=title,
                    created_at=datetime.now(),
                )
                session.add(chat)
                await session.commit()
                await session.refresh(chat)
                return chat
            except Exception as e:
                print(str(e))
                await session.rollback()
                raise e
