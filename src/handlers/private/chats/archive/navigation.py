"""Archive navigation handlers."""

from __future__ import annotations

import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import chat_actions_ikb, chats_management_ikb
from services import ChatService
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
)
async def archive_back_to_chat_actions_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик возврата к меню действий чата из архива."""
    await callback.answer()

    chat_id = await state.get_value("chat_id")
    if chat_id is None:
        logger.error("chat_id не найден в state")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chats_management_ikb(),
        )
        return

    try:
        chat_service: ChatService = container.resolve(ChatService)
        chat = await chat_service.get_chat_with_archive(chat_id=chat_id)
    except Exception as exc:
        logger.error("Ошибка при получении чата: %s", exc)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.ERROR_GET_CHAT_WITH_ARCHIVE,
            reply_markup=chats_management_ikb(),
        )
        return

    if not chat:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chats_management_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.CHAT_ACTIONS_INFO,
        reply_markup=chat_actions_ikb(),
    )
