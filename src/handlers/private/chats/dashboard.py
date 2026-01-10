import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from container import container
from keyboards.inline.chats import (
    antibot_setting_ikb,
    chat_actions_ikb,
    chats_management_ikb,
)
from services.chat import ChatService
from states import ChatStateManager
from usecases.chat import ToggleAntibotUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(CallbackData.Chat.PREFIX_CHAT))
async def chat_selected_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик выбора чата из списка чатов.
    """
    await callback.answer()

    chat_id = int(callback.data.replace(CallbackData.Chat.PREFIX_CHAT, ""))

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

    await callback.message.edit_text(
        text=Dialog.Chat.CHAT_ACTIONS.format(
            title=chat.title,
            start_time=chat.start_time.strftime("%H:%M"),
            end_time=chat.end_time.strftime("%H:%M"),
        ),
        reply_markup=chat_actions_ikb(is_antibot_enabled=chat.is_antibot_enabled),
    )

    await state.set_state(ChatStateManager.selecting_chat)


@router.callback_query(F.data == CallbackData.Chat.ANTIBOT_SETTING)
async def antibot_menu_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик перехода в меню настройки антибота.
    """
    data = await state.get_data()
    chat_id = data.get("chat_id")

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


@router.callback_query(F.data == CallbackData.Chat.ANTIBOT_TOGGLE)
async def toggle_antibot_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик переключения системы антибота.
    """
    data = await state.get_data()
    chat_id = data.get("chat_id")

    if not chat_id:
        await callback.answer("Ошибка: чат не выбран", show_alert=True)
        return

    toggle_usecase: ToggleAntibotUseCase = container.resolve(ToggleAntibotUseCase)
    new_state = await toggle_usecase.execute(chat_id=chat_id)

    if new_state is None:
        await callback.answer("Ошибка: чат не найден", show_alert=True)
        return

    chat_service: ChatService = container.resolve(ChatService)
    chat = await chat_service.get_chat_with_archive(chat_id=chat_id)

    status_text = Dialog.Antibot.ENABLED if new_state else Dialog.Antibot.DISABLED
    await callback.answer(
        Dialog.Antibot.TOGGLE_SUCCESS.format(chat_title=chat.title, status=status_text)
    )

    status_icon = "✅" if new_state else "❌"
    display_status = "Включен" if new_state else "Выключен"

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=f"🛡️ <b>Настройка Антибота для чата {chat.title}</b>\n\n"
        f"Текущий статус: {status_icon} <b>{display_status}</b>\n\n"
        f"Система Антибота ограничивает новых участников (mute), пока они не пройдут "
        f"проверку в личных сообщениях бота.",
        reply_markup=antibot_setting_ikb(is_enabled=new_state),
    )
