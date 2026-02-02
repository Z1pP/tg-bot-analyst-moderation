import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import chat_actions_ikb
from services.chat import ChatService
from states import ChatStateManager, RatingStateManager
from utils.send_message import safe_edit_message

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
    ChatStateManager.selecting_period,
)
@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
    RatingStateManager.selecting_period,
)
@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
    RatingStateManager.selecting_custom_period,
)
async def back_to_chat_actions_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик возврата к меню чатов."""
    await callback.answer()

    chat_id = await state.get_value("chat_id")

    chat_service: ChatService = container.resolve(ChatService)
    chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

    if not chat:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
            reply_markup=chat_actions_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.CHAT_ACTIONS_INFO.format(
            title=chat.title,
            start_time=chat.start_time.strftime("%H:%M"),
            end_time=chat.end_time.strftime("%H:%M"),
        ),
        reply_markup=chat_actions_ikb(),
    )

    await state.set_state(ChatStateManager.selecting_chat)
