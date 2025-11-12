import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from container import container
from dto.message_action import MessageActionDTO
from exceptions.moderation import MessageDeleteError
from keyboards.inline.message_actions import message_action_ikb, send_message_ikb
from states.message_management import MessageManagerState
from usecases.admin_actions import DeleteMessageUseCase
from utils.state_logger import log_and_set_state

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    MessageManagerState.waiting_delete_confirm,
    F.data.in_(["delete_message_confirm", "delete_message_cancel"]),
)
async def message_delete_confirm_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик подтверждения удаления сообщения."""
    await callback.answer()

    if callback.data == "delete_message_cancel":
        # Возвращаемся к окну действий над сообщением
        data = await state.get_data()
        chat_tgid = data.get("chat_tgid")
        message_id = data.get("message_id")

        if not chat_tgid or not message_id:
            logger.warning("Некорректные данные в state при отмене удаления: %s", data)
            # Если нет данных, возвращаемся в меню управления сообщениями
            await callback.message.edit_text(
                text=f"{Dialog.MessageManager.DELETE_CANCELLED}\n\n{Dialog.MessageManager.INPUT_MESSAGE_LINK}",
                reply_markup=send_message_ikb(),
            )
            await state.update_data(active_message_id=callback.message.message_id)
            await log_and_set_state(
                callback.message, state, MessageManagerState.waiting_message_link
            )
            return

        await callback.message.edit_text(
            text=Dialog.MessageManager.MESSAGE_ACTIONS.format(
                message_id=message_id,
                chat_tgid=chat_tgid,
            ),
            reply_markup=message_action_ikb(),
        )

        await log_and_set_state(
            callback.message, state, MessageManagerState.waiting_action_select
        )

        logger.info(
            "Админ %s отменил удаление и вернулся к окну действий с сообщением",
            callback.from_user.id,
        )
        return

    data = await state.get_data()
    chat_tgid = data.get("chat_tgid")
    message_id = data.get("message_id")

    if not chat_tgid or not message_id:
        logger.error("Некорректные данные в state: %s", data)
        await callback.message.edit_text(
            Dialog.MessageManager.INVALID_STATE_DATA
        )
        await state.clear()
        return

    dto = MessageActionDTO(
        chat_tgid=chat_tgid,
        message_id=message_id,
        admin_tgid=str(callback.from_user.id),
        admin_username=callback.from_user.username or "unknown",
    )

    usecase: DeleteMessageUseCase = container.resolve(DeleteMessageUseCase)

    try:
        await usecase.execute(dto)
        # После успешного удаления возвращаемся в меню управления сообщениями
        success_text = f"{Dialog.MessageManager.DELETE_SUCCESS}\n\n{Dialog.MessageManager.INPUT_MESSAGE_LINK}"
        await callback.message.edit_text(
            text=success_text,
            reply_markup=send_message_ikb(),
        )
        # Сохраняем message_id для последующего редактирования
        await state.update_data(active_message_id=callback.message.message_id)
        await log_and_set_state(
            callback.message, state, MessageManagerState.waiting_message_link
        )
        logger.info(
            "Админ %s удалил сообщение %s из чата %s",
            callback.from_user.id,
            message_id,
            chat_tgid,
        )
    except MessageDeleteError as e:
        # При ошибке удаления также возвращаемся в меню управления сообщениями
        error_text = f"{e.get_user_message()}\n\n{Dialog.MessageManager.INPUT_MESSAGE_LINK}"
        await callback.message.edit_text(
            text=error_text,
            reply_markup=send_message_ikb(),
        )
        await state.update_data(active_message_id=callback.message.message_id)
        await log_and_set_state(
            callback.message, state, MessageManagerState.waiting_message_link
        )
    except Exception as e:
        logger.error(
            "Ошибка удаления сообщения %s: %s",
            message_id,
            e,
            exc_info=True,
        )
        # При ошибке также возвращаемся в меню управления сообщениями
        error_text = f"{Dialog.MessageManager.DELETE_ERROR}\n\n{Dialog.MessageManager.INPUT_MESSAGE_LINK}"
        await callback.message.edit_text(
            text=error_text,
            reply_markup=send_message_ikb(),
        )
        await state.update_data(active_message_id=callback.message.message_id)
        await log_and_set_state(
            callback.message, state, MessageManagerState.waiting_message_link
        )
