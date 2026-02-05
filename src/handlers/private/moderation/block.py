"""Модуль хендлеров для блокировки пользователей.

Содержит логику для инициации блокировки, ввода данных пользователя,
указания причины и выбора чатов для применения наказания.
"""

import logging

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog, InlineButtons
from constants.punishment import PunishmentActions as Actions
from keyboards.inline.moderation import (
    no_reason_ikb,
)
from states import BanUserStates
from usecases.moderation import GiveUserBanUseCase

from .helpers import (
    execute_moderation_logic,
    handle_reason_input_logic,
    handle_user_search_logic,
    setup_user_input_view,
)

router = Router()
logger = logging.getLogger(__name__)
block_buttons = InlineButtons.Moderation()


@router.callback_query(F.data == InlineButtons.Moderation.BLOCK_USER)
async def block_start_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Инициализирует процесс блокировки пользователя.

    Args:
        callback: Объект callback-запроса от кнопки 'Блокировка'.
        state: Контекст состояния FSM.

    State:
        Устанавливает: BanUserStates.waiting_user_input.
    """
    await setup_user_input_view(
        callback=callback,
        state=state,
        next_state=BanUserStates.waiting_user_input,
        dialog_text=Dialog.BanUser.INPUT_USER_DATA,
    )


@router.message(BanUserStates.waiting_user_input)
async def block_user_input_handler(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
    container: Container,
) -> None:
    """Обрабатывает ввод данных пользователя для блокировки.

    Args:
        message: Сообщение с username или ID пользователя.
        state: Контекст состояния FSM.
        bot: Экземпляр бота.
        container: DI-контейнер.

    State:
        Ожидает: BanUserStates.waiting_user_input.
        Устанавливает: BanUserStates.waiting_reason_input при успехе.
    """
    await handle_user_search_logic(
        message=message,
        state=state,
        bot=bot,
        container=container,
        dialog_texts={
            "invalid_format": Dialog.User.INVALID_USERNAME_FORMAT_ADD,
            "user_not_found": Dialog.BanUser.USER_NOT_FOUND,
            "user_info": Dialog.BanUser.USER_INFO,
        },
        success_keyboard=no_reason_ikb,
        next_state=BanUserStates.waiting_reason_input,
    )


@router.message(BanUserStates.waiting_reason_input)
async def block_reason_input_handler(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
    container: Container,
) -> None:
    """Обрабатывает текстовый ввод причины блокировки.

    Args:
        message: Сообщение с текстом причины.
        state: Контекст состояния FSM.
        bot: Экземпляр бота.
        container: DI-контейнер.

    State:
        Ожидает: BanUserStates.waiting_reason_input.
        Устанавливает: BanUserStates.waiting_chat_select при наличии доступных чатов.
    """
    reason = message.text.strip()

    await handle_reason_input_logic(
        reason=reason,
        sender=message,
        state=state,
        bot=bot,
        container=container,
        is_callback=False,
        next_state=BanUserStates.waiting_chat_select,
    )


@router.callback_query(
    BanUserStates.waiting_reason_input,
    F.data == block_buttons.NO_REASON,
)
async def block_no_reason_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    bot: Bot,
    container: Container,
) -> None:
    """Обрабатывает выбор блокировки без указания причины.

    Args:
        callback: Объект callback-запроса от кнопки 'Без причины'.
        state: Контекст состояния FSM.
        bot: Экземпляр бота.
        container: DI-контейнер.

    State:
        Ожидает: BanUserStates.waiting_reason_input.
        Устанавливает: BanUserStates.waiting_chat_select при наличии доступных чатов.
    """
    await callback.answer()

    await handle_reason_input_logic(
        reason=None,
        sender=callback,
        state=state,
        bot=bot,
        container=container,
        is_callback=True,
        next_state=BanUserStates.waiting_chat_select,
    )


@router.callback_query(
    BanUserStates.waiting_chat_select,
    F.data.startswith("chat__"),
)
async def block_chat_select_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обрабатывает выбор чата для применения блокировки.

    Args:
        callback: Объект callback-запроса с ID чата.
        state: Контекст состояния FSM.
        container: DI-контейнер.

    State:
        Ожидает: BanUserStates.waiting_chat_select.
    """
    await execute_moderation_logic(
        callback=callback,
        state=state,
        action=Actions.BAN,
        usecase_cls=GiveUserBanUseCase,
        success_text=Dialog.BanUser.SUCCESS_BAN,
        partial_text=Dialog.BanUser.PARTIAL_BAN,
        fail_text=Dialog.BanUser.FAIL_BAN,
        container=container,
    )
