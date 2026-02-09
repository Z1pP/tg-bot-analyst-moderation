"""Модуль хендлеров для выдачи предупреждений пользователям.

Содержит логику для инициации выдачи варна, ввода данных пользователя,
указания причины и выбора чатов для применения наказания.
"""

import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog, InlineButtons
from constants.callback import CallbackData
from constants.punishment import PunishmentActions as Actions
from keyboards.inline.moderation import (
    no_reason_ikb,
)
from states import WarnUserStates
from usecases.moderation import GiveUserWarnUseCase

from .helpers import (
    execute_moderation_logic,
    handle_reason_input_logic,
    handle_user_search_logic,
    setup_user_input_view,
)

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data == InlineButtons.Moderation.WARN_USER)
async def warn_start_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Инициализирует процесс выдачи предупреждения пользователю.

    Args:
        callback: Объект callback-запроса от кнопки 'Предупреждение'.
        state: Контекст состояния FSM.

    State:
        Устанавливает: WarnUserStates.waiting_user_input.
    """
    await setup_user_input_view(
        callback=callback,
        state=state,
        next_state=WarnUserStates.waiting_user_input,
        dialog_text=Dialog.WarnUser.INPUT_USER_DATA,
    )


@router.message(WarnUserStates.waiting_user_input)
async def warn_user_input_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
    container: Container,
) -> None:
    """Обрабатывает ввод данных пользователя для выдачи предупреждения.

    Args:
        message: Сообщение с username или ID пользователя.
        state: Контекст состояния FSM.
        bot: Экземпляр бота.
        container: DI-контейнер.

    State:
        Ожидает: WarnUserStates.waiting_user_input.
        Устанавливает: WarnUserStates.waiting_reason_input при успехе.
    """
    await handle_user_search_logic(
        message=message,
        state=state,
        bot=bot,
        container=container,
        dialog_texts={
            "invalid_format": Dialog.WarnUser.INVALID_USER_DATA_FORMAT,
            "user_not_found": Dialog.WarnUser.USER_NOT_FOUND,
            "user_info": Dialog.WarnUser.USER_INFO,
        },
        success_keyboard=no_reason_ikb,
        next_state=WarnUserStates.waiting_reason_input,
    )


@router.message(WarnUserStates.waiting_reason_input)
async def warn_reason_input_handler(
    message: Message,
    state: FSMContext,
    bot: Bot,
    container: Container,
) -> None:
    """Обрабатывает текстовый ввод причины предупреждения.

    Args:
        message: Сообщение с теклем причины.
        state: Контекст состояния FSM.
        bot: Экземпляр бота.
        container: DI-контейнер.

    State:
        Ожидает: WarnUserStates.waiting_reason_input.
        Устанавливает: WarnUserStates.waiting_chat_select при наличии доступных чатов.
    """
    reason = message.text.strip()

    await handle_reason_input_logic(
        reason=reason,
        sender=message,
        state=state,
        bot=bot,
        container=container,
        is_callback=False,
        next_state=WarnUserStates.waiting_chat_select,
        action=Actions.WARNING,
    )


@router.callback_query(
    WarnUserStates.waiting_reason_input,
    F.data == CallbackData.Moderation.NO_REASON,
)
async def warn_no_reason_handler(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    container: Container,
) -> None:
    """Обрабатывает выбор предупреждения без указания причины.

    Args:
        callback: Объект callback-запроса от кнопки 'Без причины'.
        state: Контекст состояния FSM.
        bot: Экземпляр бота.
        container: DI-контейнер.

    State:
        Ожидает: WarnUserStates.waiting_reason_input.
        Устанавливает: WarnUserStates.waiting_chat_select при наличии доступных чатов.
    """
    await callback.answer()

    await handle_reason_input_logic(
        reason=None,
        sender=callback,
        state=state,
        bot=bot,
        container=container,
        is_callback=True,
        next_state=WarnUserStates.waiting_chat_select,
        action=Actions.WARNING,
    )


@router.callback_query(
    WarnUserStates.waiting_chat_select,
    F.data.startswith("chat__"),
)
async def warn_chat_select_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обрабатывает выбор чата для выдачи предупреждения.

    Args:
        callback: Объект callback-запроса с ID чата.
        state: Контекст состояния FSM.
        container: DI-контейнер.

    State:
        Ожидает: WarnUserStates.waiting_chat_select.
    """
    await execute_moderation_logic(
        callback=callback,
        state=state,
        action=Actions.WARNING,
        usecase_cls=GiveUserWarnUseCase,
        success_text=Dialog.WarnUser.SUCCESS_WARN,
        partial_text=Dialog.WarnUser.PARTIAL_WARN,
        fail_text=Dialog.WarnUser.FAIL_WARN,
        container=container,
    )
