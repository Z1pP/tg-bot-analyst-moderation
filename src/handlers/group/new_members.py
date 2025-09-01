import logging

from aiogram import F, Router, types

from container import container
from usecases.user import GetOrCreateUserIfNotExistUserCase
from utils.exception_handler import handle_exception

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def get_or_create_user(tg_id: str, username: str) -> None:
    """Создает или получает пользователя из базы данных."""
    try:
        usecase: GetOrCreateUserIfNotExistUserCase = container.resolve(
            GetOrCreateUserIfNotExistUserCase
        )
        user = await usecase.execute(tg_id=tg_id, username=username)
        logger.info(
            f"Пользователь {username} (ID: {tg_id}) {'создан' if not user.is_existed else 'найден'}"
        )
        return user
    except Exception as e:
        logger.error(f"Ошибка при создании/получении пользователя {username}: {e}")


@router.message(F.new_chat_members)
async def process_new_chat_members(message: types.Message):
    """Обработчик добавления новых участников в группу."""
    try:
        chat_title = message.chat.title or "Неизвестная группа"
        logger.info(
            f"Новые участники в группе '{chat_title}': {len(message.new_chat_members)}"
        )

        for user in message.new_chat_members:
            username = user.username or user.first_name or f"user_{user.id}"

            if user.is_bot:
                if user.id == message.bot.id:
                    logger.info(
                        f"Наш бот добавлен в группу '{chat_title}' (ID: {message.chat.id})"
                    )
                else:
                    logger.info(f"Бот {username} добавлен в группу '{chat_title}'")
            else:
                logger.info(
                    f"Пользователь {username} (ID: {user.id}) добавлен в группу '{chat_title}'"
                )
                await get_or_create_user(
                    tg_id=str(user.id),
                    username=username,
                )

        logger.info(
            f"Обработка {len(message.new_chat_members)} новых участников завершена"
        )

    except Exception as e:
        await handle_exception(message, e, "process_new_chat_members")


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
        await handle_exception(message, e, "process_left_chat_member")
