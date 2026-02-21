"""Обработчик проверки прав бота в чате через Telegram API."""

import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import (
    back_to_chat_actions_only_ikb,
    chat_actions_ikb,
    chats_menu_ikb,
)
from states import ChatStateManager
from usecases.permissions import GetBotPermissionsInChatUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Chat.CHECK_PERMISSIONS,
    ChatStateManager.selecting_chat,
)
async def check_permissions_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """
    Обработчик проверки прав бота в чате.
    Запрашивает данные через Telegram API и выводит подробный отчёт.
    """
    await callback.answer()

    chat_id = await state.get_value("chat_id")
    if chat_id is None:
        logger.warning("chat_id не найден в state при проверке прав")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chats_menu_ikb(),
        )
        return

    usecase: GetBotPermissionsInChatUseCase = container.resolve(
        GetBotPermissionsInChatUseCase
    )
    result = await usecase.execute(chat_id=chat_id)

    if not result.success:
        if result.error_key == "chat_not_found":
            text = Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED
            reply_markup = chat_actions_ikb()
        else:
            text = Dialog.Chat.PERMISSIONS_CHECK_ERROR
            reply_markup = back_to_chat_actions_only_ikb()
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=text,
            reply_markup=reply_markup,
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=result.text,
        reply_markup=back_to_chat_actions_only_ikb(),
    )
