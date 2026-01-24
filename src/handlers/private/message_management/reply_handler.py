import logging

from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from dto.message_action import MessageActionDTO
from exceptions.moderation import MessageSendError
from keyboards.inline.message_actions import send_message_ikb
from states.message_management import MessageManagerState
from usecases.admin_actions import ReplyToMessageUseCase
from utils.send_message import safe_edit_message

router = Router()
logger = logging.getLogger(__name__)


@router.message(MessageManagerState.waiting_reply_message)
async def message_reply_handler(
    message: types.Message, state: FSMContext, bot: Bot, container: Container
) -> None:
    """Обработчик получения контента для ответа."""
    data = await state.get_data()
    chat_tgid = data.get("chat_tgid")
    message_id = data.get("message_id")
    active_message_id = data.get("active_message_id")

    if not chat_tgid or not message_id:
        logger.error("Некорректные данные в state: %s", data)
        await message.reply(Dialog.Messages.INVALID_STATE_DATA)
        await state.clear()
        return

    dto = MessageActionDTO(
        chat_tgid=chat_tgid,
        message_id=message_id,
        admin_tgid=str(message.from_user.id),
        admin_username=message.from_user.username or "unknown",
        admin_message_id=message.message_id,
    )

    try:
        usecase: ReplyToMessageUseCase = container.resolve(ReplyToMessageUseCase)
        await usecase.execute(dto)

        # Удаляем сообщение пользователя с контентом только после успешной отправки
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение пользователя: {e}")
        success_text = (
            f"{Dialog.Messages.REPLY_SUCCESS}\n\n{Dialog.Messages.INPUT_MESSAGE_LINK}"
        )

        # Редактируем существующее сообщение или отправляем новое
        if active_message_id:
            await safe_edit_message(
                bot=bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=success_text,
                reply_markup=send_message_ikb(),
            )
        else:
            sent_msg = await message.answer(
                success_text, reply_markup=send_message_ikb()
            )
            await state.update_data(active_message_id=sent_msg.message_id)

        await state.set_state(MessageManagerState.waiting_message_link)

        logger.info(
            "Админ %s ответил на сообщение %s в чате %s",
            message.from_user.id,
            message_id,
            chat_tgid,
        )
    except MessageSendError as e:
        error_text = f"{e.get_user_message()}\n\n{Dialog.Messages.INPUT_MESSAGE_LINK}"
        if active_message_id:
            await safe_edit_message(
                bot=bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=error_text,
                reply_markup=send_message_ikb(),
            )
        else:
            sent_msg = await message.answer(error_text, reply_markup=send_message_ikb())
            await state.update_data(active_message_id=sent_msg.message_id)
        await state.set_state(MessageManagerState.waiting_message_link)
    except Exception as e:
        logger.error(
            "Ошибка отправки ответа на сообщение %s: %s",
            message_id,
            e,
            exc_info=True,
        )
        error_text = (
            f"{Dialog.Messages.REPLY_ERROR}\n\n{Dialog.Messages.INPUT_MESSAGE_LINK}"
        )
        if active_message_id:
            await safe_edit_message(
                bot=bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=error_text,
                reply_markup=send_message_ikb(),
            )
        else:
            sent_msg = await message.answer(error_text, reply_markup=send_message_ikb())
            await state.update_data(active_message_id=sent_msg.message_id)

        await state.set_state(MessageManagerState.waiting_message_link)
