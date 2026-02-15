import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto.message_action import MessageActionDTO
from states.message_management import (
    MessageManagerState,
    get_message_action_state,
)
from usecases.admin_actions import DeleteMessageUseCase

from .helpers import (
    execute_message_action_and_show_menu,
    show_message_actions_menu,
    show_message_management_menu,
)

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(
    MessageManagerState.waiting_confirm,
    F.data.in_(
        [
            CallbackData.Messages.DELETE_MESSAGE_CONFIRM,
            CallbackData.Messages.DELETE_MESSAGE_CANCEL,
        ]
    ),
)
async def confirm_handler(
    callback: types.CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обработчик подтверждения удаления сообщения."""
    await callback.answer()

    action_state = await get_message_action_state(state)
    active_message_id = (
        action_state.active_message_id if action_state else callback.message.message_id
    )

    if callback.data == CallbackData.Messages.DELETE_MESSAGE_CANCEL:
        if not action_state:
            logger.warning("Некорректные данные в state при отмене удаления")
            await show_message_management_menu(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=active_message_id,
                state=state,
                text_prefix=Dialog.Messages.DELETE_CANCELLED,
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
            "Админ %s отменил удаление и вернулся к окну действий с сообщением",
            callback.from_user.id,
        )
        return

    if not action_state:
        logger.error("Некорректные данные в state при подтверждении удаления")
        await show_message_management_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=Dialog.Messages.INVALID_STATE_DATA,
        )
        return

    dto = MessageActionDTO(
        chat_tgid=action_state.chat_tgid,
        message_id=action_state.message_id,
        admin_tgid=str(callback.from_user.id),
        admin_username=callback.from_user.username or "unknown",
    )

    usecase: DeleteMessageUseCase = container.resolve(DeleteMessageUseCase)
    success = await execute_message_action_and_show_menu(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=action_state.active_message_id,
        state=state,
        usecase=usecase,
        dto=dto,
        success_text=Dialog.Messages.DELETE_SUCCESS,
        generic_error_text=Dialog.Messages.DELETE_ERROR,
    )
    if success:
        logger.info(
            "Админ %s удалил сообщение %s из чата %s",
            callback.from_user.id,
            action_state.message_id,
            action_state.chat_tgid,
        )
