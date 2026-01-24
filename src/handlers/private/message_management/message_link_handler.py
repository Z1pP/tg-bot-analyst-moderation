import logging

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from keyboards.inline.message_actions import message_action_ikb, send_message_ikb
from states.message_management import MessageManagerState
from utils.data_parser import MESSAGE_LINK_PATTERN, parse_message_link
from utils.send_message import safe_edit_message

router = Router()
logger = logging.getLogger(__name__)


@router.message(
    F.text.regexp(MESSAGE_LINK_PATTERN),
    MessageManagerState.waiting_message_link,
)
async def message_link_handler(
    message: types.Message, state: FSMContext, bot: Bot
) -> None:
    """Обработчик ссылки на сообщение."""
    result = parse_message_link(message.text)

    # Получаем message_id активного сообщения для редактирования
    data = await state.get_data()
    active_message_id = data.get("active_message_id")

    if not result:
        # Если ссылка неверная, удаляем сообщение пользователя и показываем ошибку
        if active_message_id:
            await safe_edit_message(
                bot=bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=f"{Dialog.Messages.INVALID_LINK}\n\n{Dialog.Messages.INPUT_MESSAGE_LINK}",
                reply_markup=send_message_ikb(),
            )
        else:
            await message.reply(Dialog.Messages.INVALID_LINK)

        # Удаляем сообщение пользователя со ссылкой
        try:
            await message.delete()
        except Exception as e:
            logger.warning(f"Не удалось удалить сообщение: {e}")
        return

    chat_tgid, message_id = result

    logger.info(
        "Админ %s запросил действия для сообщения %s в чате %s",
        message.from_user.id,
        message_id,
        chat_tgid,
    )

    await state.update_data(
        chat_tgid=chat_tgid,
        message_id=message_id,
    )

    # Удаляем сообщение пользователя со ссылкой
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")

    # Редактируем существующее сообщение вместо создания нового
    text = Dialog.Messages.MESSAGE_ACTIONS.format(
        message_id=message_id,
        chat_tgid=chat_tgid,
    )

    if active_message_id:
        await safe_edit_message(
            bot=bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=text,
            reply_markup=message_action_ikb(),
        )
    else:
        # Если нет active_message_id, отправляем новое сообщение
        sent_msg = await message.answer(
            text,
            reply_markup=message_action_ikb(),
        )
        await state.update_data(active_message_id=sent_msg.message_id)

    await state.set_state(MessageManagerState.waiting_action_select)
