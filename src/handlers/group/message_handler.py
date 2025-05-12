import enum

from aiogram import Router
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from dto.message import CreateMessageDTO, CreateMessageReplyDTO
from filters.group_filter import GroupTypeFilter
from models import ChatSession, ModeratorActivity, User

router = Router(name=__name__)

"""
1. Приходит сообщение в обработчик
2. Бот понимает от кого это сообщение 
3. Бот понимает что за тип сообщения
4. Если это просто сообщение (не reply):
    - Сообщение сохраняется в БД
    - Трекается активность в БД также
5. Если сообщение reply то:
    - Сообщение сохраняется в БД reply 
    - Трекается активность в БД также
"""


class MessageType(enum.Enum):
    REPLY = "reply"
    MESSAGE = "message"


def _get_message_type(message: Message) -> MessageType:
    if message.reply_to_message:
        return MessageType.REPLY
    else:
        return MessageType.MESSAGE


@router.message(GroupTypeFilter())
async def group_message_handler(message: Message, **data):
    """
    Обрабатывет сообщения которые приходит только от модераторов чата
    """
    moderator: User = data.get("moderator")
    chat: ChatSession = data.get("chat")

    if not moderator or not chat:
        return

    msg_type = _get_message_type(message=message)

    # Если модератор сделал ответ на сообщение то
    # фиксируем это MessageReply + ModeratorActivity
    if msg_type == MessageType.REPLY:
        reply_msg_dto = CreateMessageReplyDTO(
            original_message_id=message.reply_to_message.message_id,
            reply_message_id=message.message_id,
            original_user_id=message.reply_to_message.from_user.id,
            reply_user_id=message.from_user.id,
        )
        await process_moderator_reply(message, moderator)

    # Если это обычное сообщение то
    # фиксируем это Message + ModeratorActivity
    else:
        msg_dto = CreateMessageDTO(
            chat_id=chat.id,
            user_id=moderator.id,
            message_id=message.message_id,
            message_type=message.content_type,
            text=message.text,
        )
        await precess_moderator_message(message, moderator)


async def process_moderator_reply(reply_dto: CreateMessageReplyDTO):
    # Получаем данные о сообщении
    pass


async def precess_moderator_message(msg_dto: CreateMessageDTO):
    """Обрабатывает сообщения которые не являются reply"""
    pass


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
