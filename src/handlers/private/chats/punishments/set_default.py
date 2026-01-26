import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import (
    chats_menu_ikb,
    confirm_set_default_punishments_ikb,
)
from usecases.punishment import SetDefaultPunishmentLadderUseCase
from utils.send_message import safe_edit_message

from .settings import punishment_settings_handler

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.PUNISHMENT_SET_DEFAULT)
async def set_default_punishments_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
):
    """Сброс до настроек по умолчанию"""
    await callback.answer()

    data = await state.get_data()

    chat_id = data.get("chat_id")
    if not chat_id:
        logger.error("chat_db_id не найден в state")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chats_menu_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Punishment.CONFIRM_SET_DEFAULT,
        reply_markup=confirm_set_default_punishments_ikb(),
    )


@router.callback_query(
    F.data.in_(
        [
            CallbackData.Chat.CONFIRM_SET_DEFAULT,
            CallbackData.Chat.CANCEL_SET_DEFAULT,
        ]
    )
)
async def confirm_set_default_punishments_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
):
    """Подтверждение сброса до настроек по умолчанию"""

    data = await state.get_data()
    chat_id = data.get("chat_id")
    admin_tgid = str(callback.from_user.id)
    action = callback.data.split("_")[-1]
    confirm = action == "confirm"

    try:
        usecase: SetDefaultPunishmentLadderUseCase = container.resolve(
            SetDefaultPunishmentLadderUseCase
        )
        result = await usecase.execute(
            chat_id=chat_id,
            admin_tgid=admin_tgid,
            confirm=confirm,
        )
        if result.success:
            if confirm:
                await callback.answer(Dialog.Punishment.SUCCESS_SET_DEFAULT)
            else:
                await callback.answer(Dialog.Punishment.ACTION_CANCELLED)
            await punishment_settings_handler(
                callback=callback, state=state, container=container
            )
        else:
            await callback.answer(
                result.error_message or Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED
            )
    except Exception as e:
        logger.error("Error setting default punishments: %s", e)
        await callback.answer(Dialog.Punishment.ERROR_SET_DEFAULT, show_alert=True)
