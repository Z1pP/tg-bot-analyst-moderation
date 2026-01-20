import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from punq import Container

from constants import Dialog
from filters.admin_filter import AdminOnlyFilter
from filters.group_filter import GroupTypeFilter
from handlers.group.common import send_notification, send_permission_error
from keyboards.inline.chats import hide_notification_ikb, move_to_chat_analytics_ikb
from usecases.chat_tracking import AddChatToTrackResult, AddChatToTrackUseCase

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(Command("track"), GroupTypeFilter(), AdminOnlyFilter())
async def add_chat_to_tracking_handler(message: Message, container: Container) -> None:
    """Обработчик команды /track для добавления чата в отслеживание."""
    admin_user = message.from_user
    chat = message.chat

    logger.info(
        "Команда /track от %s (ID: %s) в чате '%s' (ID: %s)",
        admin_user.username,
        admin_user.id,
        chat.title,
        chat.id,
    )

    try:
        usecase: AddChatToTrackUseCase = container.resolve(AddChatToTrackUseCase)
        result = await usecase.execute(
            admin_tg_id=str(admin_user.id),
            chat_tg_id=str(chat.id),
            chat_title=chat.title,
            admin_username=admin_user.username,
        )

        if not result.success:
            await _handle_error(message, result)
            return

        if result.is_already_tracked:
            await _send_already_tracked_notification(message, result.chat.id)
            return

        await _send_success_notification(message, result.chat.title, result.chat.id)

    except Exception as e:
        logger.error("Ошибка в chat_added_to_tracking_handler: %s", e, exc_info=True)
    finally:
        await message.delete()


async def _handle_error(message: Message, result: AddChatToTrackResult) -> None:
    """Обработка ошибок при добавлении чата."""
    if result.permissions_check and not result.permissions_check.has_all_permissions:
        await send_permission_error(
            bot=message.bot,
            admin_telegram_id=message.from_user.id,
            admin_username=message.from_user.username or "Admin",
            bot_status_is_member=result.permissions_check.is_member,
            reply_markup=hide_notification_ikb(),
        )
    else:
        logger.error(
            "Ошибка при добавлении чата в отслеживание: %s", result.error_message
        )


async def _send_already_tracked_notification(message: Message, chat_id: int) -> None:
    """Уведомление о том, что чат уже отслеживается."""
    await send_notification(
        bot=message.bot,
        chat_id=message.from_user.id,
        message_text=Dialog.Chat.CHAT_ALREADY_TRACKED,
        reply_markup=move_to_chat_analytics_ikb(chat_id=chat_id),
    )


async def _send_success_notification(
    message: Message, chat_title: str, chat_id: int
) -> None:
    """Уведомление об успешном добавлении чата."""
    await send_notification(
        bot=message.bot,
        chat_id=message.from_user.id,
        message_text=Dialog.Chat.SUCCESS_ADD_CHAT_TO_TRACKING.format(
            chat_title=chat_title,
        ),
        reply_markup=move_to_chat_analytics_ikb(chat_id=chat_id),
    )
