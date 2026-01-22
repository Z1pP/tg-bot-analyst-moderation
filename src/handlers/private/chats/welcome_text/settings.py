import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import chats_management_ikb
from services.chat import ChatService
from utils.send_message import safe_edit_message

from .helpers import build_welcome_text_view

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.WELCOME_TEXT_SETTING)
async def welcome_text_settings_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик нажатия на кнопку настройки приветственного текста"""
    await callback.answer()

    chat_id = await state.get_value("chat_id")
    if not chat_id:
        logger.error("chat_id не найден в state")
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

    if chat is None:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chats_management_ikb(),
        )
        return

    text, reply_markup = build_welcome_text_view(chat)
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=reply_markup,
    )
