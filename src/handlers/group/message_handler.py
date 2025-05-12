from aiogram import Router
from aiogram.types import Message
from punq import Container
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.session import async_session
from dto.chat import ChatDTO
from dto.message import MessageDTO
from dto.user import UserDTO
from filters.group_filter import GroupTypeFilter
from models import ChatMessage, ChatSession, ModeratorActivity, User
from models.user import UserRole

# from usecases.user.get_or_create_user import GetOrCreateUserIfNotExistUserCase

router = Router(name=__name__)

"""
1. Приходит сообщение с обработчик
2. Бот понимает от кого это сообщение 
3. Бот понимает что за тип сообщения
4. Если это просто сообщение (не reply):
    - Сообщение сохраняется в БД
    - Трекается активность в БД также
5. Если сообщение reply то:
    - Сообщение сохраняется в БД reply 
    - Трекается активность в БД также
"""


@router.message(GroupTypeFilter())
async def message_handler(message: Message, container: Container):
    message_dto = MessageDTO(
        user=UserDTO(
            tg_id=message.from_user.id,
            username=message.from_user.username,
        ),
        chat=ChatDTO(
            chat_id=message.chat.id,
            title=message.chat.title,
        ),
        message_id=message.message_id,
        text=message.text,
        message_type=message.content_type,
        reply_to_message_id=message.reply_to_message.message_id
        if message.reply_to_message
        else None,
    )

    # usercase: GetOrCreateUserIfNotExistUserCase = container.resolve(
    #     GetOrCreateUserIfNotExistUserCase
    # )
    # user = await usercase.execute(
    #     tg_id=message.from_user.id, username=message.from_user.username
    # )

    # # Получение chat_id
    # chat_id = message.chat.id

    # # Если модератор сделал ответ на сообщение то
    # # фиксируем это MessageReply + ModeratorActivity
    # if message.reply_to_message:
    #     await message.answer("Это сообщение было ответом на другое сообщение")

    # # Если это обычное сообщение то
    # # фиксируем это Message + ModeratorActivity
    # else:
    #     await
    #     await message.answer("Это обычное сообщение")

    # return


# ------------------------------------------------------
async def save_message(message: Message):
    # Ищем пользователя
    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.tg_id == str(message.from_user.id))
        )
        user = result.scalars().first()

        if not user:
            user = User(
                tg_id=str(message.from_user.id),
                username=message.from_user.username,
                role=UserRole.ADMIN,
            )

            try:
                session.add(user)
                await session.commit()
                await session.refresh(user)
            except Exception as e:
                session.rollback()
                print(str(e))
                raise e

        # Ищем чат
        try:
            chat = await session.execute(
                select(ChatSession).where(ChatSession.chat_id == str(message.chat.id))
            )
            chat = chat.scalars().first()
        except Exception as e:
            print(str(e))
            raise e

        if not chat:
            chat = ChatSession(
                chat_id=str(message.chat.id),
                title=message.chat.title,
            )
            try:
                session.add(chat)
                await session.commit()
                await session.refresh(chat)
            except Exception as e:
                await session.rollback()
                print(str(e))

        # Делаем запись по новому сообщению
        new_message = ChatMessage(
            chat_id=chat.id,
            user_id=user.id,
            message_id=str(message.message_id),
            message_type=message.content_type,
            text=message.text,
        )

        try:
            session.add(new_message)
            await session.commit()
            await session.refresh(new_message)
        except Exception as e:
            await session.rollback()
            print(str(e))

        last_message = await _get_last_activity(session, user.id, chat.id)
        if not last_message:
            return new_message
        inactive_perion = await _get_inactive_perion(last_message, new_message)
        await _create_activity_record(
            session, user.id, chat.id, last_message.id, new_message.id, inactive_perion
        )

        return new_message


async def _get_inactive_perion(
    last_message: ChatMessage, next_message: ChatMessage
) -> int:
    perion = next_message.created_at - last_message.created_at
    return perion.seconds


async def _get_last_activity(session: AsyncSession, user_id: int, chat_id: int):
    """Получение последнего сообщения"""
    try:
        return await session.scalar(
            select(ChatMessage)
            .where(
                ChatMessage.user_id == user_id,
                ChatMessage.chat_id == chat_id,
            )
            .order_by(ChatMessage.created_at.desc())
            .limit(1)
            .offset(1)
        )
    except Exception as e:
        print(str(e))
        raise e


async def _create_activity_record(
    session: AsyncSession,
    user_id: int,
    chat_id: int,
    last_message_id: int,
    next_message_id: int,
    inacvive_period: int,
):
    """Создание записи активности конкретного модератора"""
    activity = ModeratorActivity(
        moderator_id=user_id,
        chat_id=chat_id,
        last_message_id=last_message_id,
        next_message_id=next_message_id,
        inactive_period_seconds=inacvive_period,
    )

    try:
        session.add(activity)
        await session.commit()
        await session.refresh(activity)
        return activity
    except Exception as e:
        print(str(e))
        session.rollback()
        raise e
