import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from punq import Container

from constants import Dialog
from filters.admin_filter import AdminOnlyFilter
from filters.group_filter import GroupTypeFilter
from handlers.group.common import send_notification, send_permission_error
from keyboards.inline.chats import move_to_chat_analytics_ikb
from keyboards.inline.menu import close_ikb
from usecases.chat_tracking import AddChatToTrackUseCase

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(Command("track"), GroupTypeFilter(), AdminOnlyFilter())
async def chat_added_to_tracking_handler(
    message: Message, container: Container
) -> None:
    """Обработчик команды /track для добавления чата в отслеживание."""

    logger.info(
        f"Получена команда /track от {message.from_user.username} "
        f"в чате '{message.chat.title}' (ID: {message.chat.id})"
    )

    try:
        # Добавляем чат в отслеживание через UseCase
        usecase: AddChatToTrackUseCase = container.resolve(AddChatToTrackUseCase)
        result = await usecase.execute(
            admin_tg_id=str(message.from_user.id),
            chat_tg_id=str(message.chat.id),
            chat_title=message.chat.title,
            admin_username=message.from_user.username,
        )

        if not result.success:
            if (
                result.permissions_check
                and not result.permissions_check.has_all_permissions
            ):
                await send_permission_error(
                    bot=message.bot,
                    admin_telegram_id=message.from_user.id,
                    admin_username=message.from_user.username or "Admin",
                    chat_title=message.chat.title or "Без названия",
                    chat_tg_id=str(message.chat.id),
                    bot_status_is_member=result.permissions_check.is_member,
                    bot_status_text=result.permissions_check.status,
                    reply_markup=close_ikb(),
                )
            else:
                logger.error(
                    f"Ошибка при добавлении чата в отслеживание: {result.error_message}"
                )
            return

        admin = result.admin
        chat = result.chat

        if result.is_already_tracked:
            await send_already_tracked_notification(
                message=message,
                admin_username=admin.username or "Admin",
                chat_id=chat.id,
            )
            return

        logger.info(
            f"Чат '{chat.title}' успешно добавлен "
            f"в отслеживание админом {admin.username}"
        )

        await send_admin_notification(
            message=message,
            admin_username=admin.username or "Admin",
            chat_title=chat.title,
            chat_id=chat.id,
        )
    except Exception as e:
        logger.error(f"Ошибка при обработке команды /track: {e}", exc_info=True)
    finally:
        await message.delete()


async def send_already_tracked_notification(
    message: Message,
    admin_username: str,
    chat_id: int,
) -> None:
    try:
        logger.debug(
            f"Отправка уведомления админу {admin_username} что чат уже отслеживается"
        )

        await send_notification(
            bot=message.bot,
            chat_id=message.from_user.id,
            message_text=Dialog.Chat.CHAT_ALREADY_TRACKED,
            reply_markup=move_to_chat_analytics_ikb(chat_id=chat_id),
        )

        logger.info(f"Уведомление отправлено админу {admin_username}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления что чат уже отслеживается: {e}")


async def send_admin_notification(
    message: Message,
    admin_username: str,
    chat_title: str,
    chat_id: int,
) -> None:
    try:
        logger.debug(
            "Отправка уведомления об успехе "
            f"админу {admin_username} (ID: {message.from_user.id})"
        )

        await send_notification(
            bot=message.bot,
            chat_id=message.from_user.id,
            message_text=Dialog.Chat.SUCCESS_ADD_CHAT_TO_TRACKING.format(
                chat_title=chat_title,
            ),
            reply_markup=move_to_chat_analytics_ikb(chat_id=chat_id),
        )

        logger.info(
            f"Уведомление об успешном добавлении отправлено админу {admin_username}"
        )

    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления об успехе: {e}")
