from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.users_chats_settings import first_time_setup_ikb
from states.first_time_setup import FirstTimeSetupStates
from utils.send_message import safe_edit_message

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.UserAndChatsSettings.FIRST_TIME_SETTINGS)
async def first_time_settings_handler(
    callback: CallbackQuery, state: FSMContext
) -> None:
    """
    Обработчик нажатия на кнопку первоначальной настройки
    (начать настройку или вернуться в меню настроек пользователей и чатов).
    """
    await callback.answer()

    await state.set_state(FirstTimeSetupStates.waiting_chat_bound)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.UserAndChatsSettings.CHAT_BOUND_TEXT.format(
            instruction=Dialog.Chat.ADD_CHAT_INSTRUCTION
        ),
        reply_markup=first_time_setup_ikb(),
    )


@router.callback_query(
    F.data == CallbackData.UserAndChatsSettings.CONTINUE_SETTINGS,
    FirstTimeSetupStates.waiting_chat_bound,
)
async def process_chat_bound(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик нажатия на кнопку продолжить настройку после привязки чата
    (начать настройку пользователя или вернуться в меню настроек пользователей и чатов).
    """
    await callback.answer()

    message = await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.UserAndChatsSettings.USER_ADD_TEXT.format(
            instruction=Dialog.User.ADD_USER_INSTRUCTION
        ),
    )
    await state.update_data(active_message_id=message.message_id)

    await state.set_state(FirstTimeSetupStates.waiting_user_added)
