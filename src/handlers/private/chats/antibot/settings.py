"""Antibot menu handler."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import chats_menu_ikb
from usecases.antibot import GetAntibotSettingsUseCase
from utils.send_message import safe_edit_callback_message

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Chat.ANTIBOT_SETTING)
async def antibot_settings_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """
    Обработчик перехода в меню настройки антибота.
    """
    chat_id = await state.get_value("chat_id")

    if not chat_id:
        await safe_edit_callback_message(
            callback=callback,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chats_menu_ikb(),
        )
        return

    usecase: GetAntibotSettingsUseCase = container.resolve(GetAntibotSettingsUseCase)
    result = await usecase.execute(chat_id=chat_id)

    await safe_edit_callback_message(
        callback=callback,
        text=result.text,
        reply_markup=result.reply_markup,
    )
