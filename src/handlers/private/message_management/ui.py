from aiogram import Bot
from aiogram.fsm.context import FSMContext

from constants import Dialog
from keyboards.inline.message_actions import message_action_ikb, send_message_ikb
from states.message_management import MessageManagerState
from utils.send_message import safe_edit_message


async def show_message_management_menu(
    bot: Bot,
    chat_id: int,
    message_id: int,
    state: FSMContext,
    text_prefix: str = "",
) -> None:
    """Показывает главное меню управления сообщениями (ввод ссылки)."""
    text = Dialog.Messages.INPUT_MESSAGE_LINK
    if text_prefix:
        text = f"{text_prefix}\n\n{text}"

    await safe_edit_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=send_message_ikb(),
    )

    await state.update_data(active_message_id=message_id)
    await state.set_state(MessageManagerState.waiting_message_link)


async def show_message_actions_menu(
    bot: Bot,
    chat_id: int,
    message_id: int,
    state: FSMContext,
    chat_tgid: str,
    tg_message_id: int,
) -> None:
    """Показывает меню действий с конкретным сообщением (удалить/ответить)."""
    text = Dialog.Messages.MESSAGE_ACTIONS.format(
        message_id=tg_message_id,
        chat_tgid=chat_tgid,
    )

    await safe_edit_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=message_action_ikb(),
    )

    await state.update_data(
        active_message_id=message_id,
        chat_tgid=chat_tgid,
        message_id=tg_message_id,
    )
    await state.set_state(MessageManagerState.waiting_action_select)
