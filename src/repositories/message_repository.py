from typing import Optional

from sqlalchemy import select

from database.session import async_session
from models import ChatMessage


class MessageRepository:
    async def get_last_user_message(
        self, user_id: int, chat_id: int
    ) -> Optional[ChatMessage]:
        async with async_session() as session:
            try:
                return await session.scalar(
                    select(ChatMessage)
                    .where(
                        ChatMessage.user_id == user_id,
                        ChatMessage.chat_id == chat_id,
                    )
                    .order_by(ChatMessage.id.desc())
                    .limit(1)
                    .offset(1)
                )
            except Exception as e:
                print(str(e))
                return None

    async def create_new_message(
        self, user_id: int, chat_id: int, message_id: str, message_type: str, text: str
    ) -> ChatMessage:
        async with async_session() as session:
            try:
                new_message = ChatMessage(
                    user_id=user_id,
                    chat_id=chat_id,
                    message_id=message_id,
                    message_type=message_type,
                    text=text,
                )
                session.add(new_message)
                await session.commit()
                await session.refresh(new_message)
                return new_message
            except Exception as e:
                print(str(e))
                await session.rollback()
                raise e
