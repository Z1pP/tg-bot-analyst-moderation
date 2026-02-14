import logging

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext

from utils.data_parser import MESSAGE_LINK_PATTERN, parse_message_link

from .helpers import show_message_actions_menu, show_message_management_menu

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.message(
    F.text.regexp(MESSAGE_LINK_PATTERN),
    # Ограничиваем только состоянием ожидания ссылки, чтобы не перехватывать везде
)
async def process_link_handler(
    message: types.Message, state: FSMContext, bot: Bot
) -> None:
    """Обработчик ссылки на сообщение."""
    result = parse_message_link(message.text)

    data = await state.get_data()
    active_message_id = data.get("active_message_id")

    # Удаляем сообщение пользователя для чистоты чата
    try:
        await message.delete()
    except Exception as e:
        logger.warning("Не удалось удалить сообщение пользователя: %s", e)

    if not result:
        # Если ссылка неверная, показываем ошибку в активном сообщении
        if active_message_id:
            from constants import Dialog

            await show_message_management_menu(
                bot=bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                state=state,
                text_prefix=Dialog.Messages.INVALID_LINK,
            )
        return

    chat_tgid, tg_message_id = result

    logger.info(
        "Админ %s запросил действия для сообщения %s в чате %s",
        message.from_user.id,
        tg_message_id,
        chat_tgid,
    )

    # Если есть активное сообщение, редактируем его, иначе отправляем новое
    if active_message_id:
        await show_message_actions_menu(
            bot=bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            state=state,
            chat_tgid=chat_tgid,
            tg_message_id=tg_message_id,
        )
    else:
        # Если почему-то нет active_message_id, создаем новое меню
        # Но сначала нам нужно отправить сообщение, чтобы получить его ID
        from constants import Dialog
        from keyboards.inline.message_actions import message_action_ikb
        from states.message_management import MessageManagerState

        text = Dialog.Messages.MESSAGE_ACTIONS.format(
            message_id=tg_message_id,
            chat_tgid=chat_tgid,
        )
        sent_msg = await message.answer(
            text,
            reply_markup=message_action_ikb(),
        )
        await state.update_data(
            active_message_id=sent_msg.message_id,
            chat_tgid=chat_tgid,
            message_id=tg_message_id,
        )
        await state.set_state(MessageManagerState.waiting_action_select)
