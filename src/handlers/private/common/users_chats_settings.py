from aiogram import F, Router
from aiogram.types import CallbackQuery
from punq import Container

from constants.callback import CallbackData

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.UserAndChatsSettings.SHOW_MENU)
async def users_chats_settings_handler(
    callback: CallbackQuery,
    container: Container,
):
    """Обработчик нажатия на кнопку настроек пользователей и чатов"""
    await callback.answer()
