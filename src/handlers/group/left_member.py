import logging

from aiogram import F, Router, types

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(F.left_chat_member)
async def process_left_chat_member(message: types.Message):
    """Обработчик выхода участника из группы."""
    try:
        chat_title = message.chat.title or "Неизвестная группа"
        left_user = message.left_chat_member
        username = left_user.username or left_user.first_name or f"user_{left_user.id}"

        if left_user.is_bot:
            if left_user.id == message.bot.id:
                logger.info(
                    f"Наш бот удален из группы '{chat_title}' (ID: {message.chat.id})"
                )
            else:
                logger.info(f"Бот {username} покинул группу '{chat_title}'")
        else:
            logger.info(
                f"Пользователь {username} (ID: {left_user.id}) покинул группу '{chat_title}'"
            )

    except Exception as e:
        logger.error(
            f"Ошибка при обработке выхода участника из группы: {e}", exc_info=True
        )
