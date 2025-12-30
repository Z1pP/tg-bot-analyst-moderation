import logging

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog, InlineButtons
from constants.punishment import PunishmentActions as Actions
from keyboards.inline.banhammer import (
    no_reason_ikb,
)
from states import BanUserStates, ModerationStates
from usecases.moderation import GiveUserBanUseCase

from .common import (
    process_moderation_action,
    process_reason_common,
    process_user_handler_common,
    process_user_input_common,
)

router = Router()
logger = logging.getLogger(__name__)
block_buttons = InlineButtons.BlockButtons()


@router.callback_query(
    F.data == block_buttons.BLOCK_USER,
    ModerationStates.menu,
)
async def block_user_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик для блокировки пользователя.
    """
    await process_user_handler_common(
        callback=callback,
        state=state,
        next_state=BanUserStates.waiting_user_input,
        dialog_text=Dialog.BanUser.INPUT_USER_DATA,
    )


@router.message(BanUserStates.waiting_user_input)
async def process_user_data_input(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """
    Обработчик для получения данных о пользователе.
    """
    await process_user_input_common(
        message=message,
        state=state,
        bot=bot,
        dialog_texts={
            "invalid_format": Dialog.User.INVALID_USERNAME_FORMAT,
            "user_not_found": Dialog.BanUser.USER_NOT_FOUND,
            "user_info": Dialog.BanUser.USER_INFO,
        },
        success_keyboard=no_reason_ikb,
        next_state=BanUserStates.waiting_reason_input,
        error_state=ModerationStates.menu,
    )


@router.message(BanUserStates.waiting_reason_input)
async def process_reason_input(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Обработка причины блокировки (введённой вручную)."""
    reason = message.text.strip()

    await process_reason_common(
        reason=reason,
        sender=message,
        state=state,
        bot=bot,
        is_callback=False,
        next_state=BanUserStates.waiting_chat_select,
    )


@router.callback_query(
    BanUserStates.waiting_reason_input,
    F.data == block_buttons.NO_REASON,
)
async def process_no_reason(
    callback: types.CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Обработка нажатия кнопки 'Без причины'."""
    await callback.answer()

    await process_reason_common(
        reason=None,
        sender=callback,
        state=state,
        bot=bot,
        is_callback=True,
        next_state=BanUserStates.waiting_chat_select,
    )


@router.callback_query(
    BanUserStates.waiting_chat_select,
    F.data.startswith("chat__"),
)
async def process_chat_selection(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """
    Обработчик для выбора чата для блокировки.
    """
    await process_moderation_action(
        callback=callback,
        state=state,
        action=Actions.BAN,
        usecase_cls=GiveUserBanUseCase,
        success_text=Dialog.BanUser.SUCCESS_BAN,
        partial_text=Dialog.BanUser.PARTIAL_BAN,
        fail_text=Dialog.BanUser.FAIL_BAN,
    )
