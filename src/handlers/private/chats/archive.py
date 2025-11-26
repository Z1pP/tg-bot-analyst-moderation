import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from constants.callback import CallbackData
from container import container
from keyboards.inline.chats import archive_channel_setting_ikb, chats_management_ikb
from services import ChatService
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == CallbackData.Chat.ARCHIVE_SETTING,
)
async def archive_channel_setting_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик настроек архивного чата."""
    chat_id = await state.get_value("chat_id")

    try:
        chat_service: ChatService = container.resolve(ChatService)
        chat = await chat_service.get_chat_with_archive(chat_id=chat_id)
    except Exception as e:
        logger.error("Ошибка при получении чата: %s", e)
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

    if chat.archive_chat:
        text = Dialog.Chat.ARCHIVE_CHANNEL_EXISTS.format(title=chat.title)
    else:
        text = Dialog.Chat.ARCHIVE_CHANNEL_MISSING.format(title=chat.title)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=archive_channel_setting_ikb(
            archive_chat=chat.archive_chat or None,
        ),
    )
