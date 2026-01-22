"""Antibot menu handler."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import antibot_setting_ikb, chats_management_ikb
from services.chat import ChatService
from utils.send_message import safe_edit_message

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Chat.ANTIBOT_SETTING)
async def antibot_menu_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """
    Обработчик перехода в меню настройки антибота.
    """
    chat_id = await state.get_value("chat_id")

    if not chat_id:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chats_management_ikb(),
        )
        return

    chat_service: ChatService = container.resolve(ChatService)
    chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

    if not chat:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chats_management_ikb(),
        )
        return

    antibot_status = "🟢 Включён" if chat.is_antibot_enabled else "🔴 Выключен"
    welcome_text_status = "🟢 Включён" if chat.welcome_text else "🔴 Выключен"

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Antibot.SETTINGS_INFO.format(
            chat_title=chat.title,
            antibot_status=antibot_status,
            welcome_text_status=welcome_text_status,
        ),
        reply_markup=antibot_setting_ikb(is_enabled=chat.is_antibot_enabled),
    )
