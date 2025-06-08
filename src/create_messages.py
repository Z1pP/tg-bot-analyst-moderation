import asyncio
from datetime import datetime
from random import randint

from database.session import async_session
from dto.message import CreateMessageDTO
from models.message import ChatMessage
from services.time_service import TimeZoneService


async def main():
    dt = datetime(2025, 6, 2, 13, 30, 0)
    random_id = str(randint(100, 999))
    dto = CreateMessageDTO(
        chat_id=1,
        user_id=1,
        message_id=random_id,
        message_type="message",
        content_type="text",
        created_at=TimeZoneService.convert_to_local_time(dt),
        text=f"test message {random_id}",
    )

    async with async_session() as session:
        try:
            new_message = ChatMessage(
                user_id=dto.user_id,
                chat_id=dto.chat_id,
                message_id=dto.message_id,
                message_type=dto.message_type,
                content_type=dto.content_type,
                text=dto.text,
                created_at=dto.created_at,
            )
            session.add(new_message)
            await session.commit()
            await session.refresh(new_message)
            return new_message
        except Exception as e:
            print(str(e))
            await session.rollback()
            raise e


if __name__ == "__main__":
    asyncio.run(main())
