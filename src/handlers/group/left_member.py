import logging

from aiogram import Bot, F, Router, types
from aiogram.enums import ChatType
from aiogram.filters import IS_MEMBER, IS_NOT_MEMBER, ChatMemberUpdatedFilter
from punq import Container

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.chat_member(
    ChatMemberUpdatedFilter(IS_MEMBER >> IS_NOT_MEMBER),
    F.chat.type.in_([ChatType.GROUP, ChatType.SUPERGROUP]),
)
async def process_chat_member_left(
    event: types.ChatMemberUpdated,
    container: Container,
    bot: Bot,
) -> None:
    """Обработчик выхода участника из группы (ChatMemberUpdated)."""
    try:
        chat_title = event.chat.title or "Неизвестная группа"
        left_user = event.old_chat_member.user
        username = left_user.username or left_user.first_name or f"user_{left_user.id}"

        if left_user.is_bot:
            bot_info = await bot.get_me()
            if left_user.id == bot_info.id:
                logger.info(
                    "Наш бот удален из группы '%s' (ID: %s)",
                    chat_title,
                    event.chat.id,
                )
            else:
                logger.info("Бот %s покинул группу '%s'", username, chat_title)
        else:
            logger.info(
                "Пользователь %s (ID: %s) покинул группу '%s'",
                username,
                left_user.id,
                chat_title,
            )

    except Exception as e:
        logger.error(
            "Ошибка при обработке выхода участника из группы: %s", e, exc_info=True
        )
