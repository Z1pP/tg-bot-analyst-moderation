import logging

from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from exceptions.base import BotBaseException
from handlers._handler_errors import raise_business_logic
from keyboards.inline.chats import chats_menu_ikb
from keyboards.inline.menu import main_menu_ikb
from keyboards.inline.users import hide_notification_ikb
from usecases.user import GetUserByTgIdUseCase
from utils.send_message import safe_edit_message

logger = logging.getLogger(__name__)


async def show_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
    user_language: str,
    container: Container,
) -> None:
    """Показывает главное меню и очищает состояние FSM."""
    await state.clear()

    try:
        usecase: GetUserByTgIdUseCase = container.resolve(GetUserByTgIdUseCase)
        user = await usecase.execute(tg_id=str(callback.from_user.id))
    except BotBaseException as e:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=e.get_user_message(),
            reply_markup=hide_notification_ikb(),
        )
        return
    except Exception as e:
        raise_business_logic(
            "Ошибка при получении пользователя.",
            "Произошла ошибка при получении пользователя.",
            e,
            logger,
        )

    if not user:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.User.ERROR_GET_USER,
            reply_markup=hide_notification_ikb(),
        )
        return

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
    """Показывает меню управления чатами и очищает состояние FSM."""
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.SELECT_ACTION,
        reply_markup=chats_menu_ikb(),
    )
