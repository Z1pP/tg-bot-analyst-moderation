from aiogram import F, Router
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import chats_menu_ikb
from usecases.chat_tracking.get_user_tracked_chats import GetUserTrackedChatsUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Chat.MANAGEMENT)
async def chats_management_handler(
    callback: CallbackQuery,
    container: Container = None,
):
    """Обработчик меню управления чатами"""
    await callback.answer()

    get_user_tracked_chats_usecase: GetUserTrackedChatsUseCase = container.resolve(
        GetUserTrackedChatsUseCase
    )

    tracked_chats = await get_user_tracked_chats_usecase.execute(
        tg_id=str(callback.from_user.id)
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.SELECT_ACTION,
        reply_markup=chats_menu_ikb(
            has_tracked_chats=tracked_chats.total_count > 0,
            callback_data=CallbackData.Moderation.SHOW_MENU,
        ),
    )
