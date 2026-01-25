import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from keyboards.inline.message_actions import (
    cancel_reply_ikb,
    confirm_delete_ikb,
    message_action_ikb,
    send_message_ikb,
)
from states.message_management import MessageManagerState
from utils.send_message import safe_edit_message

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    MessageManagerState.waiting_action_select,
    F.data.in_(["delete_message", "reply_message", "cancel"]),
)
async def message_action_select_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик выбора действия с сообщением."""
    await callback.answer()

    if callback.data == "delete_message":
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Messages.DELETE_CONFIRM,
            reply_markup=confirm_delete_ikb(),
        )
        await state.set_state(MessageManagerState.waiting_confirm)
        logger.info("Админ %s запросил удаление сообщения", callback.from_user.id)

    elif callback.data == "reply_message":
        # Сохраняем message_id для последующего возврата к окну действий
        await state.update_data(active_message_id=callback.message.message_id)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Messages.REPLY_INPUT,
            reply_markup=cancel_reply_ikb(),
        )
        await state.set_state(MessageManagerState.waiting_reply_message)
        logger.info("Админ %s запросил ответ на сообщение", callback.from_user.id)

    elif callback.data == "cancel":
        # Возвращаем меню управления сообщениями
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=f"{Dialog.Messages.ACTION_CANCELLED}\n\n{Dialog.Messages.INPUT_MESSAGE_LINK}",
            reply_markup=send_message_ikb(),
        )
        # Сохраняем message_id для последующего редактирования
        await state.update_data(active_message_id=callback.message.message_id)
        await state.set_state(MessageManagerState.waiting_message_link)
        logger.info(
            "Админ %s отменил действие и вернулся в меню управления сообщениями",
            callback.from_user.id,
        )


@router.callback_query(
    F.data == "cancel_reply_message",
    MessageManagerState.waiting_reply_message,
)
async def cancel_reply_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик отмены ответа на сообщение."""
    await callback.answer()

    data = await state.get_data()
    chat_tgid = data.get("chat_tgid")
    message_id = data.get("message_id")

    if not chat_tgid or not message_id:
        logger.warning("Некорректные данные в state при отмене ответа: %s", data)
        # Если нет данных, возвращаемся в меню управления сообщениями
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Messages.INPUT_MESSAGE_LINK,
            reply_markup=send_message_ikb(),
        )
        await state.update_data(active_message_id=callback.message.message_id)
        await state.set_state(MessageManagerState.waiting_message_link)
        return

    # Возвращаемся к окну действий с сообщением
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Messages.MESSAGE_ACTIONS.format(
            message_id=message_id,
            chat_tgid=chat_tgid,
        ),
        reply_markup=message_action_ikb(),
    )

    await state.set_state(MessageManagerState.waiting_action_select)

    logger.info(
        "Админ %s отменил ввод ответа и вернулся к окну действий с сообщением",
        callback.from_user.id,
    )
