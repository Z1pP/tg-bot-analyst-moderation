import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from keyboards.inline.chats import chats_menu_ikb
from keyboards.inline.menu import main_menu_ikb
from keyboards.inline.users import hide_notification_ikb
from services.user import UserService
from utils.send_message import safe_edit_message

logger = logging.getLogger(__name__)


async def show_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
    user_language: str,
    container: Container,
) -> None:
    """Helper to show the main menu and clear state."""
    await state.clear()

    try:
        user_service: UserService = container.resolve(UserService)
        user = await user_service.get_user(tg_id=str(callback.from_user.id))
    except Exception as e:
        logger.error("Error getting user: %s", e)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.User.ERROR_GET_USER,
            reply_markup=hide_notification_ikb(),
        )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Menu.MENU_TEXT.format(username=user.username),
        reply_markup=main_menu_ikb(
            user=user,
            user_language=user_language,
        ),
    )


async def show_chats_menu(callback: CallbackQuery, state: FSMContext) -> None:
    """Helper to show the chats management menu and clear state."""
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.SELECT_ACTION,
        reply_markup=chats_menu_ikb(),
    )
