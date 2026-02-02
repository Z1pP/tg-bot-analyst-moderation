from aiogram import F, Router
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.users_chats_settings import users_chats_settings_ikb
from states.first_time_setup import FirstTimeSetupStates
from usecases.chat_tracking import GetUserTrackedChatsUseCase
from usecases.user_tracking import HasTrackedUsersUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)


@router.callback_query(
    F.data == CallbackData.UserAndChatsSettings.SHOW_MENU,
    StateFilter(FirstTimeSetupStates),
)
async def first_time_back_to_users_chats_menu(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """При нажатии «Назад» из визарда — очистить state и показать меню настроек пользователей и чатов."""
    await callback.answer()
    await state.clear()

    has_tracked_users_usecase: HasTrackedUsersUseCase = container.resolve(
        HasTrackedUsersUseCase
    )
    get_tracked_chats_usecase: GetUserTrackedChatsUseCase = container.resolve(
        GetUserTrackedChatsUseCase
    )
    has_tracked_users = await has_tracked_users_usecase.execute(
        admin_tgid=str(callback.from_user.id)
    )
    user_tracked_chats = await get_tracked_chats_usecase.execute(
        tg_id=str(callback.from_user.id)
    )
    has_tracking = has_tracked_users or user_tracked_chats.total_count > 0
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.UserAndChatsSettings.MENU_TEXT,
        reply_markup=users_chats_settings_ikb(has_tracking=has_tracking),
    )
