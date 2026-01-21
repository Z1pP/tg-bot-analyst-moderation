"""Antibot menu handler."""

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants.callback import CallbackData
from keyboards.inline.chats import antibot_setting_ikb
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
        await callback.answer("Ошибка: чат не выбран", show_alert=True)
        return

    chat_service: ChatService = container.resolve(ChatService)
    chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

    if not chat:
        await callback.answer("Ошибка: чат не найден", show_alert=True)
        return

    status_icon = "✅" if chat.is_antibot_enabled else "❌"
    status_text = "Включен" if chat.is_antibot_enabled else "Выключен"

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"🛡️ <b>Настройка Антибота для чата {chat.title}</b>\n\n"
        f"Текущий статус: {status_icon} <b>{status_text}</b>\n\n"
        f"Система Антибота ограничивает новых участников (mute), пока они не пройдут "
        f"проверку в личных сообщениях бота.",
        reply_markup=antibot_setting_ikb(is_enabled=chat.is_antibot_enabled),
    )
