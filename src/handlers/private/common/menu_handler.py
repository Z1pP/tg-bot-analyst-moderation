import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.users import users_menu_ikb
from states import UserStateManager
from usecases.user_tracking import HasTrackedUsersUseCase
from utils.send_message import safe_edit_message

from .navigation import show_chats_menu, show_main_menu

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Menu.MAIN_MENU)
async def main_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext, user_language: str
) -> None:
    """Обработчик возврата в главное меню через callback"""
    await callback.answer()
    await show_main_menu(callback, state, user_language)


@router.callback_query(F.data == CallbackData.Menu.USERS_MENU)
async def users_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик меню пользователей через callback"""
    await callback.answer()
    await state.clear()

    usecase: HasTrackedUsersUseCase = container.resolve(HasTrackedUsersUseCase)
    has_tracked_users = await usecase.execute(admin_tgid=str(callback.from_user.id))

    message_text = Dialog.User.SELECT_ACTION

    await callback.message.edit_text(
        text=message_text,
        reply_markup=users_menu_ikb(has_tracked_users=has_tracked_users),
    )

    await state.set_state(UserStateManager.users_menu)


@router.callback_query(F.data == CallbackData.Menu.CHATS_MENU)
async def chats_menu_callback_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """Обработчик меню чатов через callback"""
    await callback.answer()
    await show_chats_menu(callback, state)


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

    await state.set_state(MessageManagerState.waiting_message_link)
