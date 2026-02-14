import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto.message_action import MessageActionDTO
from exceptions.moderation import MessageDeleteError
from states.message_management import MessageManagerState
from usecases.admin_actions import DeleteMessageUseCase

from .helpers import show_message_actions_menu, show_message_management_menu

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

    data = await state.get_data()
    chat_tgid = data.get("chat_tgid")
    tg_message_id = data.get("message_id")
    active_message_id = data.get("active_message_id") or callback.message.message_id

    if callback.data == CallbackData.Messages.DELETE_MESSAGE_CANCEL:
        # Возвращаемся к окну действий над сообщением
        if not chat_tgid or not tg_message_id:
            logger.warning("Некорректные данные в state при отмене удаления: %s", data)
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
            message_id=active_message_id,
            state=state,
            chat_tgid=chat_tgid,
            tg_message_id=tg_message_id,
        )
        logger.info(
            "Админ %s отменил удаление и вернулся к окну действий с сообщением",
            callback.from_user.id,
        )
        return

    # Логика подтверждения удаления
    if not chat_tgid or not tg_message_id:
        logger.error("Некорректные данные в state: %s", data)
        await show_message_management_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=Dialog.Messages.INVALID_STATE_DATA,
        )
        return

    dto = MessageActionDTO(
        chat_tgid=chat_tgid,
        message_id=tg_message_id,
        admin_tgid=str(callback.from_user.id),
        admin_username=callback.from_user.username or "unknown",
    )

    usecase: DeleteMessageUseCase = container.resolve(DeleteMessageUseCase)

    try:
        await usecase.execute(dto)
        # После успешного удаления возвращаемся в меню управления сообщениями
        await show_message_management_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=Dialog.Messages.DELETE_SUCCESS,
        )
        logger.info(
            "Админ %s удалил сообщение %s из чата %s",
            callback.from_user.id,
            tg_message_id,
            chat_tgid,
        )
    except MessageDeleteError as e:
        await show_message_management_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=e.get_user_message(),
        )
    except Exception as e:
        logger.error(
            "Ошибка удаления сообщения %s: %s",
            tg_message_id,
            e,
            exc_info=True,
        )
        await show_message_management_menu(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=Dialog.Messages.DELETE_ERROR,
        )
