import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog, InlineButtons
from constants.punishment import PunishmentActions as Actions
from keyboards.inline.moderation import (
    no_reason_ikb,
)
from states import ModerationStates, WarnUserStates
from usecases.moderation import GiveUserWarnUseCase

from .common import (
    process_moderation_action,
    process_reason_common,
    process_user_handler_common,
    process_user_input_common,
)

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == InlineButtons.Moderation.WARN_USER,
    ModerationStates.menu,
)
async def warn_user_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик для предупреждения пользователя."""
    await process_user_handler_common(
        callback=callback,
        state=state,
        next_state=WarnUserStates.waiting_user_input,
        dialog_text=Dialog.WarnUser.INPUT_USER_DATA,
    )


@router.message(WarnUserStates.waiting_user_input)
async def process_user_data_input(
    message: Message,
    state: FSMContext,
    bot: Bot,
    container: Container,
) -> None:
    """Обработчик для получения данных о пользователе."""
    await process_user_input_common(
        message=message,
        state=state,
        bot=bot,
        container=container,
        dialog_texts={
            "invalid_format": Dialog.User.INVALID_USERNAME_FORMAT_ADD,
            "user_not_found": Dialog.WarnUser.USER_NOT_FOUND,
            "user_info": Dialog.WarnUser.USER_INFO,
        },
        success_keyboard=no_reason_ikb,
        next_state=WarnUserStates.waiting_reason_input,
    )


@router.message(WarnUserStates.waiting_reason_input)
async def process_reason_input(
    message: Message,
    state: FSMContext,
    bot: Bot,
    container: Container,
) -> None:
    """Обработка причины предупреждения (введённой вручную)."""
    reason = message.text.strip()

    await process_reason_common(
        reason=reason,
        sender=message,
        state=state,
        bot=bot,
        container=container,
        is_callback=False,
        next_state=WarnUserStates.waiting_chat_select,
    )


@router.callback_query(
    WarnUserStates.waiting_reason_input,
    F.data == InlineButtons.Moderation.NO_REASON,
)
async def process_no_reason(
    callback: CallbackQuery,
    state: FSMContext,
    bot: Bot,
    container: Container,
) -> None:
    """Обработка нажатия кнопки 'Без причины'."""
    await callback.answer()

    await process_reason_common(
        reason=None,
        sender=callback,
        state=state,
        bot=bot,
        container=container,
        is_callback=True,
        next_state=WarnUserStates.waiting_chat_select,
    )


@router.callback_query(
    WarnUserStates.waiting_chat_select,
    F.data.startswith("chat__"),
)
async def process_chat_selection(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик для выбора чата для предупреждения."""
    await process_moderation_action(
        callback=callback,
        state=state,
        action=Actions.WARNING,
        usecase_cls=GiveUserWarnUseCase,
        success_text=Dialog.WarnUser.SUCCESS_WARN,
        partial_text=Dialog.WarnUser.PARTIAL_WARN,
        fail_text=Dialog.WarnUser.FAIL_WARN,
        container=container,
    )
