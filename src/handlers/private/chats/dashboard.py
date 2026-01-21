import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import chat_actions_ikb, chats_management_ikb
from services.chat import ChatService
from states import ChatStateManager
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(CallbackData.Chat.PREFIX_CHAT))
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
    if not chat_id_str.isdigit():
        logger.error("Некорректный ID чата в callback: %s", callback.data)
        return

    chat_id = int(chat_id_str)

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

    await state.update_data(chat_id=chat_id)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.CHAT_ACTIONS.format(
            title=chat.title,
            start_time=chat.start_time.strftime("%H:%M"),
            end_time=chat.end_time.strftime("%H:%M"),
        ),
        reply_markup=chat_actions_ikb(),
    )

    await state.set_state(ChatStateManager.selecting_chat)
