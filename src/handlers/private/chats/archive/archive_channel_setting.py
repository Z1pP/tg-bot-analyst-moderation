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
async def archive_channel_setting(
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
        text = (
            f"У Вас уже имеется привязанный архивный канал к чату <b>{chat.title}.</b>\n\n"
            "Вы можете перейти в него, нажав на кнопку с названием канала, "
            'либо же привязать другой архивный канал, нажав кнопку "Перепривязать".'
        )
    else:
        text = (
            f"У Вас нет привязанного архивного канала к чату <b>{chat.title}</b>.\n\n"
            "Пожалуйста, привяжите архивный канал, чтобы получать "
            "автоматический ежедневный отчёт со статистикой по чату."
        )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=archive_channel_setting_ikb(
            archive_chat=chat.archive_chat or None,
        ),
    )
