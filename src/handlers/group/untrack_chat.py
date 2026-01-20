import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from punq import Container

from constants import Dialog
from filters.admin_filter import AdminOnlyFilter
from filters.group_filter import GroupTypeFilter
from handlers.group.common import send_notification
from keyboards.inline.menu import close_ikb
from models import ChatSession, User
from services.chat import ChatService
from services.user import UserService
from usecases.chat_tracking import RemoveChatFromTrackingUseCase

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(Command("untrack"), GroupTypeFilter(), AdminOnlyFilter())
async def chat_removed_from_tracking_handler(
    message: Message,
    container: Container,
) -> None:
    """Обработчик команды /untrack для удаления чата из отслеживания."""

    logger.info(
        f"Получена команда /untrack от {message.from_user.username} "
        f"в чате '{message.chat.title}' (ID: {message.chat.id})"
    )

    admin, chat = await _get_admin_and_chat(message=message, container=container)

    if not admin or not chat:
        logger.error("Не удалось получить данные о пользователе или чате")
        return

    try:
        usecase: RemoveChatFromTrackingUseCase = container.resolve(
            RemoveChatFromTrackingUseCase
        )

        success, _ = await usecase.execute(user_id=admin.id, chat_id=chat.id)

        if success:
            logger.info(
                f"Чат '{chat.title}' успешно удален "
                f"из отслеживания админом {admin.username}"
            )

            notification_text = Dialog.Chat.SUCCESS_REMOVE_CHAT_FROM_TRACKING.format(
                chat_title=chat.title,
                chat_tg_id=chat.chat_id,
                admin_username=admin.username,
            )
        else:
            logger.warning(f"Чат '{chat.title}' не найден в отслеживании")

            notification_text = Dialog.Chat.CHAT_NOT_TRACKED.format(
                chat_title=chat.title,
                chat_tg_id=chat.chat_id,
            )

        await send_notification(
            bot=message.bot,
            chat_id=message.from_user.id,
            message_text=notification_text,
            reply_markup=close_ikb(),
        )

    except Exception as e:
        logger.error(f"Ошибка при обработке команды /untrack: {e}", exc_info=True)
    finally:
        await message.delete()


async def _get_admin_and_chat(
    message: Message, container: Container
) -> tuple[User, ChatSession]:
    """Получает пользователя и чат из сообщения."""

    logger.debug(f"Получение данных админа и чата для {message.from_user.username}")

    # Получаем сервисы
    user_service: UserService = container.resolve(UserService)
    chat_service: ChatService = container.resolve(ChatService)

    # Получаем пользователя и чат
    user_tg_id = str(message.from_user.id)
    chat_id = str(message.chat.id)

    if not user_tg_id:
        logger.warning("Пользователь без tg_id: %s", message.from_user.id)
        return None, None

    admin = await user_service.get_user(user_tg_id)
    if not admin:
        logger.warning("Пользователь не найден в базе данных: %s", user_tg_id)
        return None, None

    chat = await chat_service.get_or_create(
        chat_tgid=chat_id, title=message.chat.title or "Без названия"
    )
    if not chat:
        logger.error("Не удалось получить или создать чат: %s", chat_id)
        return None, None

    logger.debug(f"Данные получены: админ {admin.username}, чат '{chat.title}'")
    return admin, chat
