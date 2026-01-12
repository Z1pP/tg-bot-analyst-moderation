import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import (
    cancel_welcome_text_setting_ikb,
    chat_actions_ikb,
)
from services.chat import ChatService
from states import ChatStateManager, WelcomeTextState
from usecases.chat import UpdateChatWelcomeTextUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.WELCOME_TEXT_SETTING)
async def welcome_text_menu_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик нажатия на кнопку настройки приветственного текста"""
    await callback.answer()

    chat_id = await state.get_value("chat_id")
    if not chat_id:
        logger.error("chat_id не найден в state")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chat_actions_ikb(),
        )
        return

    msg = await callback.message.edit_text(
        text=Dialog.Chat.ENTER_WELCOME_TEXT,
        reply_markup=cancel_welcome_text_setting_ikb(),
    )

    await state.update_data(active_message_id=msg.message_id)
    await state.set_state(WelcomeTextState.waiting_welcome_text_input)


@router.message(WelcomeTextState.waiting_welcome_text_input)
async def welcome_text_input_handler(
    message: Message, state: FSMContext, container: Container
) -> None:
    """Обработчик ввода нового приветственного текста"""
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    chat_id = data.get("chat_id")

    if not chat_id:
        logger.error("chat_id не найден в state")
        await message.delete()
        return

    try:
        usecase: UpdateChatWelcomeTextUseCase = container.resolve(
            UpdateChatWelcomeTextUseCase
        )
        updated_chat = await usecase.execute(
            chat_id=chat_id,
            admin_tg_id=str(message.from_user.id),
            welcome_text=message.html_text,
        )

        if not updated_chat:
            text = "❌ Чат не найден. Попробуйте позже."
            if active_message_id:
                await safe_edit_message(
                    bot=message.bot,
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=text,
                    reply_markup=chat_actions_ikb(),
                )
            return

        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=Dialog.Chat.WELCOME_TEXT_UPDATED,
            reply_markup=chat_actions_ikb(),
        )
    except Exception as e:
        logger.error(
            "Ошибка при сохранении приветственного текста: %s", e, exc_info=True
        )
        text = "❌ Произошла ошибка при сохранении текста. Попробуйте позже."
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=text,
                reply_markup=chat_actions_ikb(),
            )
    finally:
        await message.delete()


@router.callback_query(
    F.data == CallbackData.Chat.BACK_TO_CHAT_ACTIONS,
    WelcomeTextState.waiting_welcome_text_input,
)
async def back_to_chat_actions_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик возврата к меню чатов из настройки приветственного текста."""
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
        text=Dialog.Chat.CHAT_ACTIONS.format(
            title=chat.title,
            start_time=chat.start_time.strftime("%H:%M"),
            end_time=chat.end_time.strftime("%H:%M"),
        ),
        reply_markup=chat_actions_ikb(),
    )

    await state.set_state(ChatStateManager.selecting_chat)
