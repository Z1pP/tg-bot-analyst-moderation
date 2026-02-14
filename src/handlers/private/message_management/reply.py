import logging

from aiogram import Bot, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from dto.message_action import MessageActionDTO
from exceptions.moderation import MessageSendError
from states.message_management import MessageManagerState
from usecases.admin_actions import ReplyToMessageUseCase

from .helpers import show_message_management_menu

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(MessageManagerState.waiting_reply_message)
async def process_reply_handler(
    message: types.Message, state: FSMContext, bot: Bot, container: Container
) -> None:
    """Обработчик получения контента для ответа."""
    # Получаем данные из state
    data = await state.get_data()
    chat_tgid = data.get("chat_tgid")
    tg_message_id = data.get("message_id")
    active_message_id = data.get("active_message_id")

    if not chat_tgid or not tg_message_id or not active_message_id:
        logger.error("Некорректные данные в state: %s", data)
        # Удаляем сообщение пользователя для чистоты чата
        try:
            await message.delete()
        except Exception as e:
            logger.warning("Не удалось удалить сообщение пользователя: %s", e)

        # Если нет active_message_id, отвечаем новым сообщением, иначе редактируем активное
        if active_message_id:
            await show_message_management_menu(
                bot=bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                state=state,
                text_prefix=Dialog.Messages.INVALID_STATE_DATA,
            )
        else:
            await message.answer(Dialog.Messages.INVALID_STATE_DATA)
            await state.clear()
        return

    dto = MessageActionDTO(
        chat_tgid=chat_tgid,
        message_id=tg_message_id,
        admin_tgid=str(message.from_user.id),
        admin_username=message.from_user.username or "unknown",
        admin_message_id=message.message_id,
    )

    try:
        usecase: ReplyToMessageUseCase = container.resolve(ReplyToMessageUseCase)
        await usecase.execute(dto)

        # После успешной отправки возвращаемся в меню управления сообщениями
        await show_message_management_menu(
            bot=bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=Dialog.Messages.REPLY_SUCCESS,
        )

        logger.info(
            "Админ %s ответил на сообщение %s в чате %s",
            message.from_user.id,
            tg_message_id,
            chat_tgid,
        )
    except MessageSendError as e:
        await show_message_management_menu(
            bot=bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=e.get_user_message(),
        )
    except Exception as e:
        logger.error(
            "Ошибка отправки ответа на сообщение %s: %s",
            tg_message_id,
            e,
            exc_info=True,
        )
        await show_message_management_menu(
            bot=bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            state=state,
            text_prefix=Dialog.Messages.REPLY_ERROR,
        )
    finally:
        try:
            await message.delete()
        except Exception as e:
            logger.warning("Не удалось удалить сообщение пользователя: %s", e)
