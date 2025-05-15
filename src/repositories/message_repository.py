from typing import Optional

from sqlalchemy import select

from database.session import async_session
from dto.message import CreateMessageDTO
from dto.message_reply import CreateMessageReplyDTO
from models import ChatMessage, MessageReply


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

    async def create_new_message(self, dto: CreateMessageDTO) -> ChatMessage:
        async with async_session() as session:
            try:
                new_message = ChatMessage(
                    user_id=dto.user_id,
                    chat_id=dto.chat_id,
                    message_id=dto.message_id,
                    message_type=dto.message_type,
                    text=dto.text,
                )
                session.add(new_message)
                await session.commit()
                await session.refresh(new_message)
                return new_message
            except Exception as e:
                print(str(e))
                await session.rollback()
                raise e

    async def create_reply_message(self, dto: CreateMessageReplyDTO) -> MessageReply:
        async with async_session() as session:
            try:
                new_reply = MessageReply(
                    chat_id=dto.chat_id,
                    original_message_url=dto.original_message_url,
                    reply_message_id=dto.reply_message_id,
                    reply_user_id=dto.reply_user_id,
                    response_time_seconds=dto.response_time_seconds,
                )
                session.add(new_reply)
                await session.commit()
                await session.refresh(new_reply)
                return new_reply
            except Exception as e:
                print(str(e))
                await session.rollback()
                raise e
