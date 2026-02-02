import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from punq import Container

from constants import Dialog
from filters.admin_filter import AdminOnlyFilter
from filters.group_filter import GroupTypeFilter
from handlers.group.common import send_notification, send_permission_error
from keyboards.inline.chats import hide_notification_ikb
from usecases.chat_tracking import (
    RemoveChatFromTrackingResult,
    RemoveChatFromTrackingUseCase,
)

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(Command("untrack"), GroupTypeFilter(), AdminOnlyFilter())
async def remove_chat_from_tracking_handler(
    message: Message,
    container: Container,
) -> None:
    """Обработчик команды /untrack для удаления чата из отслеживания."""
    admin_user = message.from_user
    chat = message.chat

    logger.info(
        "Команда /untrack от %s (ID: %s) в чате '%s' (ID: %s)",
        admin_user.username,
        admin_user.id,
        chat.title,
        chat.id,
    )

    try:
        usecase: RemoveChatFromTrackingUseCase = container.resolve(
            RemoveChatFromTrackingUseCase
        )

        result = await usecase.execute(
            admin_tg_id=str(admin_user.id),
            chat_tg_id=str(chat.id),
            chat_title=chat.title,
            admin_username=admin_user.username,
        )

        if not result.success:
            await _handle_error(message, result)
            return

        await _send_success_notification(message, result.chat.title)

    except Exception as e:
        logger.error("Ошибка в remove_chat_from_tracking_handler: %s", e, exc_info=True)
    finally:
        await message.delete()


async def _handle_error(message: Message, result: RemoveChatFromTrackingResult) -> None:
    """Обработка ошибок при удалении чата."""
    if result.permissions_check and not result.permissions_check.has_all_permissions:
        error_text = (
            Dialog.Chat.ERROR_REMOVE_CHAT_NOT_MEMBER
            if not result.permissions_check.is_member
            else Dialog.Chat.ERROR_REMOVE_CHAT_INSUFFICIENT_PERMISSIONS
        )
        await send_permission_error(
            bot=message.bot,
            admin_telegram_id=message.from_user.id,
            admin_username=message.from_user.username or "Admin",
            bot_status_is_member=result.permissions_check.is_member,
            reply_markup=hide_notification_ikb(),
            error_text=error_text,
        )
    elif result.is_chat_not_tracked:
        await send_notification(
            bot=message.bot,
            chat_id=message.from_user.id,
            message_text=Dialog.Chat.CHAT_NOT_TRACKED,
            reply_markup=hide_notification_ikb(),
        )
    else:
        logger.error(
            "Ошибка при удалении чата из отслеживания: %s", result.error_message
        )


async def _send_success_notification(message: Message, chat_title: str) -> None:
    """Уведомление об успешном удалении чата."""
    await send_notification(
        bot=message.bot,
        chat_id=message.from_user.id,
        message_text=Dialog.Chat.SUCCESS_REMOVE_CHAT_FROM_TRACKING.format(
            chat_title=chat_title
        ),
        reply_markup=hide_notification_ikb(),
    )
