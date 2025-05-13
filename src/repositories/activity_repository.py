from sqlalchemy import select

from database.session import async_session
from models import ChatMessage, MessageReply, ModeratorActivity


class ActivityRepository:
    async def create_simple_activity(
        self, message: ChatMessage, activity: ModeratorActivity
    ) -> ModeratorActivity:
        new_activity = ModeratorActivity(
            moderator_id=message.user_id,
            chat_id=message.chat_id,
            message_id=message.id,
            reply_to_message_id=None,
        )
        async with async_session() as session:
            try:
                session.add(new_activity)
                await session.commit()
                await session.refresh(new_activity)
                return activity

            except Exception as e:
                print(str(e))
                await session.rollback()
                raise e

    async def create_reply_activity(
        self, message: MessageReply, activity: ModeratorActivity
    ) -> ModeratorActivity:
        new_activity = ModeratorActivity(
            moderator_id=message.user_id,
            chat_id=message.chat_id,
            message_id=message.id,
            reply_to_message_id=message.reply_to_message_id,
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
                return await session.scalar(
                    select(ModeratorActivity).where(
                        ModeratorActivity.moderator_id == user_id,
                        ModeratorActivity.chat_id == chat_id,
                    )
                )

            except Exception as e:
                print(str(e))
                return None
