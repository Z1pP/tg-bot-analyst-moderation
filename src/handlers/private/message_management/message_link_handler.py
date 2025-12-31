import logging

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from keyboards.inline.message_actions import message_action_ikb, send_message_ikb
from states.message_management import MessageManagerState
from utils.data_parser import MESSAGE_LINK_PATTERN, parse_message_link

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

    if not result:
        # Если ссылка неверная, удаляем сообщение пользователя и показываем ошибку через edit_text
        data = await state.get_data()
        active_message_id = data.get("active_message_id")

        if active_message_id:
            try:
                await bot.edit_message_text(
                    chat_id=message.chat.id,
                    message_id=active_message_id,
                    text=f"{Dialog.MessageManager.INVALID_LINK}\n\n{Dialog.MessageManager.INPUT_MESSAGE_LINK}",
                    reply_markup=send_message_ikb(),
                )
            except Exception as e:
                logger.error(f"Ошибка при редактировании сообщения: {e}")
                await message.reply(Dialog.MessageManager.INVALID_LINK)
        else:
            await message.reply(Dialog.MessageManager.INVALID_LINK)

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

    # Получаем message_id активного сообщения для редактирования
    data = await state.get_data()
    active_message_id = data.get("active_message_id")

    # Удаляем сообщение пользователя со ссылкой
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")

    # Редактируем существующее сообщение вместо создания нового
    if active_message_id:
        try:
            await bot.edit_message_text(
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=Dialog.MessageManager.MESSAGE_ACTIONS.format(
                    message_id=message_id,
                    chat_tgid=chat_tgid,
                ),
                reply_markup=message_action_ikb(),
            )
        except Exception as e:
            logger.error(f"Ошибка при редактировании сообщения: {e}")
            # Если не удалось отредактировать, отправляем новое сообщение
            await message.answer(
                Dialog.MessageManager.MESSAGE_ACTIONS.format(
                    message_id=message_id,
                    chat_tgid=chat_tgid,
                ),
                reply_markup=message_action_ikb(),
            )
    else:
        # Если нет active_message_id, отправляем новое сообщение
        await message.answer(
            Dialog.MessageManager.MESSAGE_ACTIONS.format(
                message_id=message_id,
                chat_tgid=chat_tgid,
            ),
            reply_markup=message_action_ikb(),
        )

    await state.set_state(MessageManagerState.waiting_action_select)
