import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import (
    cancel_welcome_text_setting_ikb,
    hide_notification_ikb,
)
from states import WelcomeTextState
from usecases.chat import UpdateChatWelcomeTextUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.CHANGE_WELCOME_TEXT)
async def change_welcome_text_handler(
    callback: CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик нажатия на кнопку изменения приветственного текста"""
    await callback.answer()
    await state.set_state(WelcomeTextState.waiting_welcome_text_input)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Chat.ENTER_WELCOME_TEXT,
        reply_markup=cancel_welcome_text_setting_ikb(),
    )


@router.message(WelcomeTextState.waiting_welcome_text_input)
async def welcome_text_input_handler(
    message: Message,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик ввода нового приветственного текста"""
    data = await state.get_data()
    chat_id = data.get("chat_id")

    if not chat_id:
        await safe_edit_message(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=cancel_welcome_text_setting_ikb(),
        )
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
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=message.message_id,
                text=Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED,
                reply_markup=cancel_welcome_text_setting_ikb(),
            )
            return

        await message.answer(
            text=Dialog.Chat.WELCOME_TEXT_UPDATED,
            reply_markup=hide_notification_ikb(),
        )

    except Exception as e:
        logger.error(
            "Ошибка при сохранении приветственного текста: %s", e, exc_info=True
        )
        await message.answer(
            text=Dialog.Chat.ERROR_SAVE_WELCOME_TEXT,
            reply_markup=hide_notification_ikb(),
        )
    finally:
        await message.delete()
