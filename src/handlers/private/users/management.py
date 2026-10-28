from aiogram import F, Router
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.users import users_menu_ikb
from utils.send_message import safe_edit_callback_message

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.User.MANAGEMENT)
async def management_handler(callback: CallbackQuery) -> None:
    """Обработчик меню управления пользователями"""
    await callback.answer()

    await safe_edit_callback_message(
        callback=callback,
        text=Dialog.User.SELECT_ACTION,
        reply_markup=users_menu_ikb(
            has_tracked_users=False,
            callback_data=CallbackData.Analytics.SHOW_MENU,
        ),
    )
