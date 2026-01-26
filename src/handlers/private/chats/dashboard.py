import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import chat_actions_ikb, chats_menu_ikb
from services.chat import ChatService
from states import ChatStateManager
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data.startswith(CallbackData.Chat.PREFIX_CHAT),
    ChatStateManager.listing_tracking_chats,
)
async def chat_selected_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """
    Обработчик выбора чата из списка чатов.
    """
    await callback.answer()

    chat_id_str = callback.data.replace(CallbackData.Chat.PREFIX_CHAT, "")
    if not chat_id_str or not chat_id_str.isdigit():
        await _handle_error(callback=callback, error=ValueError("Invalid chat ID"))
        return

    chat_id = int(chat_id_str)

    chat_service: ChatService = container.resolve(ChatService)
    chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

    if not chat:
        await _show_chat_not_found_message(callback=callback)
        return

    await state.update_data(chat_id=chat_id)

    await _show_chat_actions_message(callback=callback)

    await state.set_state(ChatStateManager.selecting_chat)


async def _show_chat_not_found_message(callback: CallbackQuery) -> None:
    """Показывает сообщение о том, что чат не найден."""
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
        reply_markup=chats_menu_ikb(),
    )


async def _show_chat_actions_message(callback: CallbackQuery) -> None:
    """Показывает сообщение с информацией о действиях с чатом."""
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.CHAT_ACTIONS_INFO,
        reply_markup=chat_actions_ikb(),
    )


async def _handle_error(callback: CallbackQuery, error: Exception) -> None:
    """Обрабатывает ошибки при выборе чата."""
    logger.error("Ошибка при выборе чата: %s", error, exc_info=True)
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.ERROR_GET_CHAT_WITH_ARCHIVE,
        reply_markup=chats_menu_ikb(),
    )
