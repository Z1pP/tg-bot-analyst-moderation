"""Antibot toggle handler."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import chats_menu_ikb
from usecases.antibot import GetAntibotSettingsUseCase
from usecases.chat import ToggleAntibotUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Chat.ANTIBOT_TOGGLE)
async def toggle_antibot_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """
    Обработчик переключения системы антибота.
    """
    chat_id = await state.get_value("chat_id")

    if not chat_id:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chats_menu_ikb(),
        )
        return

    toggle_usecase: ToggleAntibotUseCase = container.resolve(ToggleAntibotUseCase)
    new_state = await toggle_usecase.execute(
        chat_id=chat_id, admin_tg_id=str(callback.from_user.id)
    )

    if new_state is None:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chats_menu_ikb(),
        )
        return

    settings_usecase: GetAntibotSettingsUseCase = container.resolve(
        GetAntibotSettingsUseCase
    )
    result = await settings_usecase.execute(chat_id=chat_id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=result.text,
        reply_markup=result.reply_markup,
    )
