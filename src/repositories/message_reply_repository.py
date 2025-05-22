from datetime import datetime

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from database.session import async_session
from dto.message_reply import CreateMessageReplyDTO
from models import MessageReply


class MessageReplyRepository:
    async def get_replies_by_user_and_period(
        self,
        user_id: int,
        start_date: datetime,
        end_date: datetime,
    ) -> list[MessageReply]:
        """
        Получает все ответы пользователя за указанный период.
        """
        async with async_session() as session:
            query = (
                select(MessageReply)
                .options(joinedload(MessageReply.chat_session))
                .where(
                    MessageReply.reply_user_id == user_id,
                    MessageReply.created_at.between(start_date, end_date),
                )
            )
            try:
                result = await session.execute(query)
                return result.scalars().all()
            except Exception as e:
                print(f"Error getting replies: {e}")
                return []

    async def create_reply_message(self, dto: CreateMessageReplyDTO) -> MessageReply:
        async with async_session() as session:
            try:
                new_reply = MessageReply(
                    chat_id=dto.chat_id,
                    original_message_url=dto.original_message_url,
                    reply_message_id=dto.reply_message_id,
                    reply_user_id=dto.reply_user_id,
                    response_time_seconds=dto.response_time_seconds,
                    created_at=datetime.now(),
                )
                session.add(new_reply)
                await session.commit()
                await session.refresh(new_reply)
                return new_reply
            except Exception as e:
                print(str(e))
                await session.rollback()
                raise e
