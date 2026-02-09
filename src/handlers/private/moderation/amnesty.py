"""Модуль хендлеров для амнистии пользователей.

Содержит логику для снятия ограничений (бан, мут) и отмены предупреждений
в одном или нескольких чатах.
"""

import logging

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog, InlineButtons
from constants.callback import CallbackData
from constants.punishment import PunishmentType
from dto import AmnestyUserDTO
from exceptions import AmnestyError
from keyboards.inline.amnesty import confirm_action_ikb
from keyboards.inline.chats import tracked_chats_with_all_ikb
from keyboards.inline.moderation import (
    amnesty_actions_ikb,
    moderation_menu_ikb,
)
from states import AmnestyStates
from usecases.amnesty import (
    CancelLastWarnUseCase,
    GetChatsWithAnyRestrictionUseCase,
    GetChatsWithMutedUserUseCase,
    GetChatsWithPunishedUserUseCase,
    UnbanUserUseCase,
    UnmuteUserUseCase,
)
from utils.formatter import format_duration
from utils.moderation import ViolatorData, extract_violator_data_from_state
from utils.send_message import safe_edit_message

from .errors import handle_chats_error
from .helpers import handle_user_search_logic, setup_user_input_view

router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(
    F.data == InlineButtons.Moderation.AMNESTY,
)
async def amnesty_start_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Инициализирует процесс амнистии пользователя.

    Args:
        callback: Объект callback-запроса от кнопки 'Амнистия'.
        state: Контекст состояния FSM.

    State:
        Устанавливает: AmnestyStates.waiting_user_input.
    """
    await setup_user_input_view(
        callback=callback,
        state=state,
        next_state=AmnestyStates.waiting_user_input,
        dialog_text=Dialog.AmnestyUser.INPUT_USER_DATA,
    )


@router.message(AmnestyStates.waiting_user_input)
async def amnesty_user_input_handler(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
    container: Container,
) -> None:
    """Обрабатывает ввод данных пользователя для амнистии.

    Args:
        message: Сообщение с username или ID пользователя.
        state: Контекст состояния FSM.
        bot: Экземпляр бота.
        container: DI-контейнер.

    State:
        Ожидает: AmnestyStates.waiting_user_input.
        Устанавливает: AmnestyStates.waiting_action_select при успехе.
    """
    await handle_user_search_logic(
        message=message,
        state=state,
        bot=bot,
        container=container,
        dialog_texts={
            "invalid_format": Dialog.WarnUser.INVALID_USER_DATA_FORMAT,
            "user_not_found": Dialog.BanUser.USER_NOT_FOUND,
            "user_info": Dialog.AmnestyUser.SELECT_ACTION,
        },
        success_keyboard=amnesty_actions_ikb,
        next_state=AmnestyStates.waiting_action_select,
        show_block_actions_on_error=True,
    )


ACTION_MAP = {
    InlineButtons.Moderation.UNBAN: Dialog.AmnestyUser.UNBAN_CONFIRMATION,
    InlineButtons.Moderation.UNMUTE: Dialog.AmnestyUser.UNMUTE_CONFIRMATION,
    InlineButtons.Moderation.CANCEL_WARN: Dialog.AmnestyUser.CANCEL_WARN_CONFIRMATION,
}


@router.callback_query(
    F.data.in_(ACTION_MAP.keys()),
    AmnestyStates.waiting_action_select,
)
async def amnesty_action_select_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обрабатывает выбор типа амнистии (разбан, размут, отмена варна).

    Args:
        callback: Объект callback-запроса с выбранным действием.
        state: Контекст состояния FSM.

    State:
        Ожидает: AmnestyStates.waiting_action_select.
        Устанавливает: AmnestyStates.waiting_confirmation_action.
    """
    await callback.answer()
    action = callback.data

    violator = await extract_violator_data_from_state(state=state)
    await state.update_data(action=action)

    await callback.message.edit_text(
        text=ACTION_MAP[action].format(username=violator.username),
        reply_markup=confirm_action_ikb(),
    )

    await state.set_state(AmnestyStates.waiting_confirmation_action)


@router.callback_query(
    F.data == CallbackData.Moderation.CONFIRM_ACTION,
    AmnestyStates.waiting_confirmation_action,
)
async def amnesty_confirm_handler(
    callback: types.CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Обрабатывает подтверждение выбранного действия амнистии.

    Args:
        callback: Объект callback-запроса подтверждения.
        state: Контекст состояния FSM.
        container: DI-контейнер.

    State:
        Ожидает: AmnestyStates.waiting_confirmation_action.
        Устанавливает: AmnestyStates.waiting_chat_select при наличии чатов с ограничениями.
    """
    await callback.answer()

    data = await state.get_data()
    action = data.get("action")

    violator = await extract_violator_data_from_state(state=state)

    amnesy_dto = AmnestyUserDTO(
        violator_tgid=violator.tg_id,
        violator_username=violator.username,
        violator_id=violator.id,
        admin_tgid=str(callback.from_user.id),
        admin_username=callback.from_user.username,
    )

    config = ACTION_CONFIG.get(action)
    if not config:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.AmnestyUser.UNKNOWN_ACTION,
            reply_markup=moderation_menu_ikb(),
        )
        return

    usecase = container.resolve(config["usecase"])

    try:
        chat_dtos = await usecase.execute(dto=amnesy_dto)
    except Exception as e:
        await handle_chats_error(callback, state, violator.username, e)
        return

    if not chat_dtos:
        await handle_chats_error(callback, state, violator.username)
        return

    text = config["text"].format(username=amnesy_dto.violator_username)
    await state.update_data(
        chat_dtos=[chat.model_dump(mode="json") for chat in chat_dtos]
    )
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=tracked_chats_with_all_ikb(dtos=chat_dtos),
    )

    await state.set_state(AmnestyStates.waiting_chat_select)


@router.callback_query(
    F.data == CallbackData.Moderation.CANCEL_ACTION,
    AmnestyStates.waiting_confirmation_action,
)
async def amnesty_cancel_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Отменяет подтверждение и возвращает к выбору типа амнистии.

    Args:
        callback: Объект callback-запроса отмены.
        state: Контекст состояния FSM.

    State:
        Ожидает: AmnestyStates.waiting_confirmation_action.
        Устанавливает: AmnestyStates.waiting_action_select.
    """
    await callback.answer()

    await callback.message.edit_text(
        text=Dialog.AmnestyUser.ACTION_CANCELLED,
        reply_markup=amnesty_actions_ikb(),
    )
    await state.set_state(AmnestyStates.waiting_action_select)


@router.callback_query(
    AmnestyStates.waiting_chat_select,
    F.data.startswith("chat__"),
)
async def amnesty_execute_handler(
    callback: types.CallbackQuery, state: FSMContext, container: Container
) -> None:
    """Выполняет выбранное действие амнистии в указанном чате (или во всех).

    Args:
        callback: Объект callback-запроса с ID чата.
        state: Контекст состояния FSM.
        container: DI-контейнер.

    State:
        Ожидает: AmnestyStates.waiting_chat_select.
        Устанавливает: AmnestyStates.waiting_action_select после выполнения.
    """
    await callback.answer()

    data = await state.get_data()

    action = data.get("action")
    chat_id_from_callback = callback.data.split("__")[1]
    chat_dtos_data = data.get("chat_dtos")

    from dto.chat_dto import ChatDTO

    chat_dtos = [ChatDTO.model_validate(chat) for chat in chat_dtos_data]

    violator = ViolatorData(
        id=data.get("id"),
        username=data.get("username"),
        tg_id=data.get("tg_id"),
    )

    if chat_id_from_callback != "all":
        chat_dtos = [
            chat for chat in chat_dtos if chat.id == int(chat_id_from_callback)
        ]

    amnesty_dto = AmnestyUserDTO(
        admin_tgid=str(callback.from_user.id),
        admin_username=callback.from_user.username,
        violator_tgid=violator.tg_id,
        violator_username=violator.username,
        violator_id=violator.id,
        chat_dtos=chat_dtos,
    )

    if action == InlineButtons.Moderation.CANCEL_WARN:
        usecase: CancelLastWarnUseCase = container.resolve(CancelLastWarnUseCase)
        try:
            result = await usecase.execute(dto=amnesty_dto)
        except AmnestyError as e:
            logger.error("Ошибка отмены предупреждения: %s", e, exc_info=True)
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=e.get_user_message(),
                reply_markup=moderation_menu_ikb(),
            )
            return

        if len(amnesty_dto.chat_dtos) == 1:
            if result.next_punishment_type == PunishmentType.BAN:
                next_step = "бессрочной блокировке."
            elif result.next_punishment_type == PunishmentType.MUTE:
                next_step = (
                    f"муту на {format_duration(result.next_punishment_duration)}"
                )
            else:
                next_step = "предупреждению."

            text = Dialog.AmnestyUser.CANCEL_WARN_SUCCESS_SINGLE.format(
                warn_count=result.current_warns_count,
                username=amnesty_dto.violator_username,
                next_step=next_step,
            )
        else:
            text = Dialog.AmnestyUser.CANCEL_WARN_SUCCESS_ALL.format(
                chats_count=len(amnesty_dto.chat_dtos),
                username=amnesty_dto.violator_username,
            )
    elif action == InlineButtons.Moderation.UNMUTE:
        usecase: UnmuteUserUseCase = container.resolve(UnmuteUserUseCase)
        try:
            await usecase.execute(dto=amnesty_dto)
        except AmnestyError as e:
            logger.error("Ошибка амнистии: %s", e, exc_info=True)
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=e.get_user_message(),
                reply_markup=moderation_menu_ikb(),
            )
            return

        text = Dialog.AmnestyUser.UNMUTE_SUCCESS.format(
            username=amnesty_dto.violator_username
        )
    elif action == InlineButtons.Moderation.UNBAN:
        usecase: UnbanUserUseCase = container.resolve(UnbanUserUseCase)
        try:
            await usecase.execute(dto=amnesty_dto)
        except AmnestyError as e:
            logger.error("Ошибка амнистии: %s", e, exc_info=True)
            await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=e.get_user_message(),
                reply_markup=moderation_menu_ikb(),
            )
            return

        text = Dialog.AmnestyUser.UNBAN_SUCCESS.format(
            username=amnesty_dto.violator_username
        )
    else:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.AmnestyUser.UNKNOWN_ACTION,
            reply_markup=moderation_menu_ikb(),
        )
        return

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=amnesty_actions_ikb(),
    )

    await state.set_state(AmnestyStates.waiting_action_select)


ACTION_CONFIG = {
    Dialog.AmnestyUser.UNBAN: {
        "usecase": GetChatsWithAnyRestrictionUseCase,
        "text": Dialog.AmnestyUser.SELECT_CHAT_UNBAN,
    },
    Dialog.AmnestyUser.UNMUTE: {
        "usecase": GetChatsWithMutedUserUseCase,
        "text": Dialog.AmnestyUser.SELECT_CHAT_UNMUTE,
    },
    Dialog.AmnestyUser.CANCEL_WARN: {
        "usecase": GetChatsWithPunishedUserUseCase,
        "text": Dialog.AmnestyUser.SELECT_CHAT_CANCEL_WARN,
    },
}
