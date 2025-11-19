import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from constants.i18n import DEFAULT_LANGUAGE
from container import container
from keyboards.inline.chats_kb import chats_menu_ikb
from keyboards.inline.menu import admin_menu_ikb
from keyboards.inline.users import users_menu_ikb
from services.user import UserService
from states import MenuStates, UserStateManager
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Menu.MAIN_MENU)
async def main_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата в главное меню через callback"""
    await callback.answer()
    await state.clear()

    username = callback.from_user.first_name
    menu_text = Dialog.MENU_TEXT.format(username=username)

    # Получаем язык пользователя из БД (LanguageMiddleware уже сохранил его)
    user_service: UserService = container.resolve(UserService)
    db_user = await user_service.get_user(tg_id=str(callback.from_user.id))
    user_language = (
        db_user.language if db_user and db_user.language else DEFAULT_LANGUAGE
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=menu_text,
        reply_markup=admin_menu_ikb(user_language, str(callback.from_user.id)),
    )

    await log_and_set_state(callback.message, state, MenuStates.main_menu)


@router.callback_query(F.data == CallbackData.Menu.USERS_MENU)
async def users_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик меню пользователей через callback"""
    await callback.answer()
    await state.clear()

    message_text = Dialog.User.SELECT_ACTION

    await callback.message.edit_text(
        text=message_text,
        reply_markup=users_menu_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=UserStateManager.users_menu,
    )


@router.callback_query(F.data == CallbackData.Menu.CHATS_MENU)
async def chats_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик меню чатов через callback"""
    await callback.answer()
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.SELECT_ACTION,
        reply_markup=chats_menu_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=MenuStates.chats_menu,
    )


@router.callback_query(F.data == CallbackData.Menu.MESSAGE_MANAGEMENT)
async def message_management_callback_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик меню управления сообщениями через callback"""
    from constants import Dialog
    from keyboards.inline.message_actions import send_message_ikb
    from states import MessageManagerState

    await callback.answer()
    await state.clear()

    logger.info(
        "Администратор %s выбрал пункт управления сообщениями",
        callback.from_user.username,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.MessageManager.INPUT_MESSAGE_LINK,
        reply_markup=send_message_ikb(),
    )

    # Сохраняем message_id для последующего редактирования
    await state.update_data(active_message_id=callback.message.message_id)

    await log_and_set_state(
        callback.message, state, MessageManagerState.waiting_message_link
    )


@router.callback_query(F.data == CallbackData.Menu.LOCK_MENU)
async def lock_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик меню блокировок через callback"""
    from constants import Dialog
    from keyboards.inline.banhammer import block_actions_ikb
    from states import BanHammerStates

    await callback.answer()
    await state.clear()

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.BlockMenu.SELECT_ACTION,
        reply_markup=block_actions_ikb(),
    )

    await log_and_set_state(callback.message, state, BanHammerStates.block_menu)
