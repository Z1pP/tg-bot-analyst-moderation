import logging
from typing import Protocol

from aiogram import Bot
from aiogram.fsm.context import FSMContext

from constants import Dialog
from dto.message_action import MessageActionDTO
from exceptions.moderation import MessageDeleteError, MessageSendError
from keyboards.inline.message_actions import message_action_ikb, send_message_ikb
from states.message_management import (
    ACTIVE_MESSAGE_ID,
    CHAT_TGID,
    MESSAGE_ID,
    MessageManagerState,
)
from utils.send_message import safe_edit_message

logger = logging.getLogger(__name__)


class MessageActionUseCaseProtocol(Protocol):
    """Протокол use case с действием над сообщением (удаление, ответ)."""

    async def execute(self, dto: MessageActionDTO) -> None: ...


async def show_message_management_menu(
    bot: Bot,
    chat_id: int,
    message_id: int,
    state: FSMContext,
    text_prefix: str = "",
) -> None:
    """Показывает главное меню управления сообщениями (ввод ссылки)."""
    text = Dialog.Messages.MESSAGE_LINK_INSTRUCTION
    if text_prefix:
        text = f"{text_prefix}\n\n{text}"

    await safe_edit_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=send_message_ikb(),
    )

    await state.update_data({ACTIVE_MESSAGE_ID: message_id})
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
        {
            ACTIVE_MESSAGE_ID: message_id,
            CHAT_TGID: chat_tgid,
            MESSAGE_ID: tg_message_id,
        }
    )
    await state.set_state(MessageManagerState.waiting_action_select)


async def execute_message_action_and_show_menu(
    bot: Bot,
    chat_id: int,
    message_id: int,
    state: FSMContext,
    usecase: MessageActionUseCaseProtocol,
    dto: MessageActionDTO,
    success_text: str,
    generic_error_text: str,
) -> bool:
    """
    Выполняет use case (удаление/ответ) и показывает меню с результатом.

    Returns:
        True при успехе, False при любой ошибке.
    """
    try:
        await usecase.execute(dto)
        await show_message_management_menu(
            bot=bot,
            chat_id=chat_id,
            message_id=message_id,
            state=state,
            text_prefix=success_text,
        )
        return True
    except (MessageDeleteError, MessageSendError) as e:
        await show_message_management_menu(
            bot=bot,
            chat_id=chat_id,
            message_id=message_id,
            state=state,
            text_prefix=e.get_user_message(),
        )
        return False
    except Exception as e:
        logger.error(
            "Ошибка действия с сообщением: %s",
            e,
            exc_info=True,
        )
        await show_message_management_menu(
            bot=bot,
            chat_id=chat_id,
            message_id=message_id,
            state=state,
            text_prefix=generic_error_text,
        )
        return False
