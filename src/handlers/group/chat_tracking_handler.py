import asyncio
import logging

from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import Message

from container import container
from filters.admin_filter import AdminOnlyFilter
from models import ChatSession, User
from services.chat import ChatService
from services.user import UserService
from usecases.chat_tracking import AddChatToTrackUseCase

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(Command("track"), AdminOnlyFilter())
async def chat_added_to_tracking_handler(message: Message, bot: Bot) -> None:
    """Обработчик команды /track для добавления чата в отслеживание."""
    if message.chat.type not in ["group", "supergroup"]:
        return

    admin, chat = await _get_admin_and_chat(message=message)

    if not admin or not chat:
        logger.error("Не удалось получить данные о пользователе или чате")
        return

    try:
        # Добавляем чат в отслеживание
        usecase: AddChatToTrackUseCase = container.resolve(AddChatToTrackUseCase)
        await usecase.execute(chat=chat, admin=admin)

        # Удаляем команду пользователя и отправляем подтверждение
        await delete_command_and_send_confirmation(message, bot)
    except Exception as e:
        logger.error("Ошибка при обработке команды /track: %s", str(e), exc_info=True)


async def delete_command_and_send_confirmation(message: Message, bot: Bot) -> None:
    """Удаляет команду пользователя и отправляет подтверждение с автоудалением."""
    try:
        # Удаляем команду пользователя
        try:
            await message.delete()
        except Exception as e:
            logger.warning("Не удалось удалить команду: %s", str(e))

        # Отправляем подтверждение
        sent_message = await bot.send_message(
            chat_id=message.chat.id,
            text="✅ <b>Чат добавлен в отслеживание</b>",
            parse_mode="HTML",
            disable_notification=True,
        )

        # Запускаем обратный отсчет и удаление
        asyncio.create_task(countdown_delete(sent_message, 5))
    except Exception as e:
        logger.error("Ошибка при отправке подтверждения: %s", str(e), exc_info=True)


async def countdown_delete(message: Message, seconds: int = 5) -> None:
    """
    Обратный отсчет с последующим удалением сообщения.

    Args:
        message: Сообщение для редактирования и удаления
        seconds: Количество секунд до удаления
    """
    await asyncio.sleep(1)

    for i in range(seconds, 0, -1):
        try:
            await message.edit_text(
                f"✅ <b>Чат добавлен в отслеживание</b>\n<i>Автоудаление через {i} сек.</i>",
                parse_mode="HTML",
            )
            await asyncio.sleep(1)
        except Exception as e:
            logger.debug("Ошибка при обновлении сообщения: %s", str(e))
            break

    try:
        await message.delete()
    except Exception as e:
        logger.debug("Не удалось удалить сообщение: %s", str(e))


async def _get_admin_and_chat(message: Message) -> tuple[User, ChatSession]:
    """
    Получает пользователя и чат из сообщения.
    """
    # Получаем сервисы
    user_service = container.resolve(UserService)
    chat_service = container.resolve(ChatService)

    # Получаем пользователя и чат
    username = message.from_user.username
    chat_id = str(message.chat.id)

    if not username:
        logger.warning("Пользователь без username: %s", message.from_user.id)
        return

    admin = await user_service.get_user(username)
    if not admin:
        logger.warning("Пользователь не найден в базе данных: %s", username)
        return

    chat = await chat_service.get_or_create_chat(
        chat_id=chat_id, title=message.chat.title or "Без названия"
    )
    if not chat:
        logger.error("Не удалось получить или создать чат: %s", chat_id)
        return

    return admin, chat
