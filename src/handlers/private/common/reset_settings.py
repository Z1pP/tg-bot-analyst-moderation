import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from handlers.private.common.users_chats_settings import (
    users_chats_settings_handler,
)
from keyboards.inline.users_chats_settings import (
    confirm_reset_ikb,
    reset_success_ikb,
    users_chats_settings_ikb,
)
from usecases.settings import ResetAllTrackingUseCase
from utils.send_message import safe_edit_message

logger = logging.getLogger(__name__)

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.UserAndChatsSettings.RESET_SETTINGS)
async def reset_settings_handler(
    callback: CallbackQuery,
) -> None:
    """Обработчик нажатия на кнопку сброса настроек (показ подтверждения)"""
    await callback.answer()

    logger.info(
        "Пользователь %s (id=%s) инициировал сброс настроек",
        callback.from_user.username,
        callback.from_user.id,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.UserAndChatsSettings.RESET_CONFIRMATION,
        reply_markup=confirm_reset_ikb(),
    )


@router.callback_query(F.data == CallbackData.UserAndChatsSettings.CANCEL_RESET)
async def cancel_reset_handler(
    callback: CallbackQuery,
) -> None:
    """Обработчик отмены сброса настроек"""
    await callback.answer()

    logger.info(
        "Пользователь %s (id=%s) отменил сброс настроек",
        callback.from_user.username,
        callback.from_user.id,
    )

    await users_chats_settings_handler(callback=callback, container=None)


@router.callback_query(F.data == CallbackData.UserAndChatsSettings.CONFIRM_RESET)
async def confirm_reset_handler(
    callback: CallbackQuery,
    container: Container,
) -> None:
    """Обработчик подтверждения сброса настроек"""
    await callback.answer()

    logger.info(
        "Пользователь %s (id=%s) подтвердил сброс настроек",
        callback.from_user.username,
        callback.from_user.id,
    )

    reset_all_tracking_usecase: ResetAllTrackingUseCase = container.resolve(
        ResetAllTrackingUseCase
    )

    try:
        await reset_all_tracking_usecase.execute(admin_tgid=str(callback.from_user.id))

        logger.info(
            "Настройки пользователя %s (id=%s) успешно сброшены",
            callback.from_user.username,
            callback.from_user.id,
        )

        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.UserAndChatsSettings.RESET_SUCCESS,
            reply_markup=reset_success_ikb(),
        )
    except Exception as e:
        logger.error(
            "Ошибка при сбросе настроек пользователя %s (id=%s): %s",
            callback.from_user.username,
            callback.from_user.id,
            e,
        )
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.UserAndChatsSettings.RESET_ERROR,
            reply_markup=users_chats_settings_ikb(has_tracking=True),
        )
