import logging

from aiogram import Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from container import container
from dto.message_action import MessageActionDTO
from exceptions.moderation import MessageSendError
from states.message_management import MessageManagerState
from usecases.admin_actions import ReplyToMessageUseCase

router = Router()
logger = logging.getLogger(__name__)


@router.message(MessageManagerState.waiting_reply_message)
async def message_reply_handler(message: types.Message, state: FSMContext) -> None:
    """Обработчик получения контента для ответа."""
    data = await state.get_data()
    chat_tgid = data.get("chat_tgid")
    message_id = data.get("message_id")

    if not chat_tgid or not message_id:
        logger.error("Некорректные данные в state: %s", data)
        await message.reply(Dialog.MessageManager.INVALID_STATE_DATA)
        await state.clear()
        return

    dto = MessageActionDTO(
        chat_tgid=chat_tgid,
        message_id=message_id,
        admin_tgid=str(message.from_user.id),
        admin_username=message.from_user.username or "unknown",
        admin_message_id=message.message_id,
    )

    usecase: ReplyToMessageUseCase = container.resolve(ReplyToMessageUseCase)

    try:
        await usecase.execute(dto)
        await message.reply(Dialog.MessageManager.REPLY_SUCCESS)
        logger.info(
            "Админ %s ответил на сообщение %s в чате %s",
            message.from_user.id,
            message_id,
            chat_tgid,
        )
    except MessageSendError as e:
        await message.reply(e.get_user_message())
    except Exception as e:
        logger.error(
            "Ошибка отправки ответа на сообщение %s: %s",
            message_id,
            e,
            exc_info=True,
        )
        await message.reply(Dialog.MessageManager.REPLY_ERROR)

    await state.clear()
