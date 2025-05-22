from datetime import datetime

from sqlalchemy import select

from database.session import async_session
from dto.activity import CreateActivityDTO
from models import MessageReply, ModeratorActivity


class ActivityRepository:
    async def create_activity(self, dto: CreateActivityDTO) -> ModeratorActivity:
        new_activity = ModeratorActivity(
            user_id=dto.user_id,
            chat_id=dto.chat_id,
            last_message_id=dto.last_message_id,
            next_message_id=dto.next_message_id,
            inactive_period_seconds=dto.inactive_period_seconds,
            created_at=datetime.now(),
        )
        async with async_session() as session:
            try:
                session.add(new_activity)
                await session.commit()
                await session.refresh(new_activity)
                return new_activity

            except Exception as e:
                print(str(e))
                await session.rollback()
                raise e

    async def create_reply_activity(
        self, message: MessageReply, activity: ModeratorActivity
    ) -> ModeratorActivity:
        new_activity = ModeratorActivity(
            user_id=message.reply_user_id,
            chat_id=message.chat_id,
            message_id=message.id,
            created_at=datetime.now(),
        )
        async with async_session() as session:
            try:
                session.add(new_activity)
                await session.commit()
                await session.refresh(new_activity)
                return activity
            # return activity.id
            except Exception as e:
                print(str(e))
                await session.rollback()
                raise e

    async def get_last_activity(self, user_id: int, chat_id: int) -> ModeratorActivity:
        async with async_session() as session:
            try:
                query = (
                    select(ModeratorActivity)
                    .where(
                        ModeratorActivity.user_id == user_id,
                        ModeratorActivity.chat_id == chat_id,
                    )
                    .order_by(ModeratorActivity.created_at.desc())
                )
                result = await session.execute(query)
                return result.scalars().first()

            except Exception as e:
                print(str(e))
                return None
