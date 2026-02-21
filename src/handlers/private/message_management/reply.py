import logging

from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from dto.message_action import MessageActionDTO
from states.message_management import (
    MessageManagerState,
    get_message_action_state,
)
from usecases.admin_actions import ReplyToMessageUseCase

from .helpers import execute_message_action_and_show_menu

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(MessageManagerState.waiting_reply_message)
async def process_reply_handler(
    message: types.Message, state: FSMContext, bot: Bot, container: Container
) -> None:
    """Обработчик получения контента для ответа."""
    action_state = await get_message_action_state(state)

    if not action_state:
        logger.error("Некорректные данные в state при ответе на сообщение")
        try:
            await message.delete()
        except Exception as e:
            logger.warning("Не удалось удалить сообщение пользователя: %s", e)
        await message.answer(Dialog.Messages.INVALID_STATE_DATA)
        await state.clear()
        return

    dto = MessageActionDTO(
        chat_tgid=action_state.chat_tgid,
        message_id=action_state.message_id,
        admin_tgid=str(message.from_user.id),
        admin_username=message.from_user.username or "unknown",
        admin_message_id=message.message_id,
    )

    usecase: ReplyToMessageUseCase = container.resolve(ReplyToMessageUseCase)
    success = await execute_message_action_and_show_menu(
        bot=bot,
        chat_id=message.chat.id,
        message_id=action_state.active_message_id,
        state=state,
        usecase=usecase,
        dto=dto,
        success_text=Dialog.Messages.REPLY_SUCCESS,
        generic_error_text=Dialog.Messages.REPLY_ERROR,
    )
    if success:
        logger.info(
            "Админ %s ответил на сообщение %s в чате %s",
            message.from_user.id,
            action_state.message_id,
            action_state.chat_tgid,
        )
    try:
        await message.delete()
    except Exception as e:
        logger.warning("Не удалось удалить сообщение пользователя: %s", e)
