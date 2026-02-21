"""Archive navigation handlers."""

from __future__ import annotations

import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto.chat_dto import GetChatWithArchiveDTO
from exceptions.base import BotBaseException
from handlers._handler_errors import raise_business_logic
from keyboards.inline.chats import chat_actions_ikb, chats_menu_ikb
from usecases.chat import GetChatWithArchiveUseCase
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
            reply_markup=chats_menu_ikb(),
        )
        return

    try:
        get_chat_uc: GetChatWithArchiveUseCase = container.resolve(
            GetChatWithArchiveUseCase
        )
        chat = await get_chat_uc.execute(GetChatWithArchiveDTO(chat_id=chat_id))
    except BotBaseException as e:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=e.get_user_message(),
            reply_markup=chats_menu_ikb(),
        )
        return
    except Exception as exc:
        raise_business_logic(
            "Ошибка при получении чата.",
            Dialog.Chat.ERROR_GET_CHAT_WITH_ARCHIVE,
            exc,
            logger,
        )

    if not chat:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chats_menu_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.CHAT_ACTIONS_INFO,
        reply_markup=chat_actions_ikb(),
    )
