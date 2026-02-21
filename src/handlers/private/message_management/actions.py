import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.message_actions import (
    cancel_reply_ikb,
    confirm_delete_ikb,
)
from states.message_management import (
    MessageManagerState,
    get_message_action_state,
)
from utils.send_message import safe_edit_message

from .helpers import show_message_actions_menu, show_message_management_menu

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    MessageManagerState.waiting_action_select,
    F.data.in_(
        [
            CallbackData.Messages.DELETE_MESSAGE,
            CallbackData.Messages.REPLY_MESSAGE,
            CallbackData.Messages.CANCEL,
        ]
    ),
)
async def select_action_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик выбора действия с сообщением."""
    await callback.answer()

    if callback.data == CallbackData.Messages.DELETE_MESSAGE:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Messages.DELETE_CONFIRM,
            reply_markup=confirm_delete_ikb(),
        )
        await state.set_state(MessageManagerState.waiting_confirm)
        logger.info("Админ %s запросил удаление сообщения", callback.from_user.id)

    elif callback.data == CallbackData.Messages.REPLY_MESSAGE:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Messages.REPLY_INPUT,
            reply_markup=cancel_reply_ikb(),
        )
        await state.set_state(MessageManagerState.waiting_reply_message)
        logger.info("Админ %s запросил ответ на сообщение", callback.from_user.id)

    elif callback.data == CallbackData.Messages.CANCEL:
        await show_message_management_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            state=state,
            text_prefix=Dialog.Messages.ACTION_CANCELLED,
        )
        logger.info(
            "Админ %s отменил действие и вернулся в меню управления сообщениями",
            callback.from_user.id,
        )


@router.callback_query(
    F.data == CallbackData.Messages.CANCEL_REPLY,
    MessageManagerState.waiting_reply_message,
)
async def cancel_reply_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик отмены ответа на сообщение."""
    await callback.answer()

    action_state = await get_message_action_state(state)
    active_message_id = (
        action_state.active_message_id if action_state else callback.message.message_id
    )

    if not action_state:
        logger.warning("Некорректные данные в state при отмене ответа")
        await show_message_management_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=active_message_id,
            state=state,
        )
        return

    await show_message_actions_menu(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=action_state.active_message_id,
        state=state,
        chat_tgid=action_state.chat_tgid,
        tg_message_id=action_state.message_id,
    )

    logger.info(
        "Админ %s отменил ввод ответа и вернулся к окну действий с сообщением",
        callback.from_user.id,
    )
