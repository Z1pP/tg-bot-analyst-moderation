import logging
from dataclasses import dataclass

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog, InlineButtons
from constants.punishment import PunishmentType
from container import container
from dto import AmnestyUserDTO
from exceptions import AmnestyError
from keyboards.inline.amnesty import confirm_action_ikb
from keyboards.inline.banhammer import (
    amnesty_actions_ikb,
    moderation_menu_ikb,
)
from keyboards.inline.chats import tracked_chats_with_all_ikb
from states import AmnestyStates, ModerationStates
from usecases.amnesty import (
    CancelLastWarnUseCase,
    GetChatsWithAnyRestrictionUseCase,
    GetChatsWithMutedUserUseCase,
    GetChatsWithPunishedUserUseCase,
    UnbanUserUseCase,
    UnmuteUserUseCase,
)
from utils.formatter import format_duration
from utils.state_logger import log_and_set_state

from .common import process_user_handler_common, process_user_input_common

router = Router()
logger = logging.getLogger(__name__)
block_buttons = InlineButtons.BlockButtons()


@router.callback_query(
    F.data == block_buttons.AMNESTY,
    ModerationStates.menu,
)
async def amnesty_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик отвечающий за действия по амнистии пользователя в чате.
    """
    await process_user_handler_common(
        callback=callback,
        state=state,
        next_state=AmnestyStates.waiting_user_input,
        dialog_text=Dialog.AmnestyUser.INPUT_USER_DATA,
    )


@router.message(AmnestyStates.waiting_user_input)
async def waiting_user_data_input(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """
    Обработчик для обработки введенной информации о пользователе
    """
    await process_user_input_common(
        message=message,
        state=state,
        bot=bot,
        dialog_texts={
            "invalid_format": Dialog.User.INVALID_USERNAME_FORMAT,
            "user_not_found": Dialog.BanUser.USER_NOT_FOUND,
            "user_info": Dialog.AmnestyUser.SELECT_ACTION,
        },
        success_keyboard=amnesty_actions_ikb,
        next_state=AmnestyStates.waiting_action_select,
        error_state=ModerationStates.menu,
        show_block_actions_on_error=True,
    )


ACTION_MAP = {
    block_buttons.UNBAN: Dialog.AmnestyUser.UNBAN_CONFIRMATION,
    block_buttons.UNMUTE: Dialog.AmnestyUser.UNMUTE_CONFIRMATION,
    block_buttons.CANCEL_WARN: Dialog.AmnestyUser.CANCEL_WARN_CONFIRMATION,
}


@router.callback_query(
    F.data.in_(ACTION_MAP.keys()),
    AmnestyStates.waiting_action_select,
)
async def amnsesy_action_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Универсальный обработчик для действий по амнистии пользователя"""
    await callback.answer()
    action = callback.data

    violator = await extract_violator_data_from_state(state=state)
    await state.update_data(action=action)

    await callback.message.edit_text(
        text=ACTION_MAP[action].format(username=violator.username),
        reply_markup=confirm_action_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=AmnestyStates.waiting_confirmation_action,
    )


@router.callback_query(
    F.data == block_buttons.CONFIRM_ACTION,
    AmnestyStates.waiting_confirmation_action,
)
async def confirm_action(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик для подтверждения действия по амнистии пользователя
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
        text = "❗️Неизвестное действие. Попробуйте еще раз."
        await callback.message.edit_text(
            text=text,
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

    text = config["text"](amnesy_dto.violator_username)
    await state.update_data(chat_dtos=chat_dtos)
    await callback.message.edit_text(
        text=text,
        reply_markup=tracked_chats_with_all_ikb(dtos=chat_dtos),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=AmnestyStates.waiting_chat_select,
    )


@router.callback_query(
    F.data == block_buttons.CANCEL_ACTION,
    AmnestyStates.waiting_confirmation_action,
)
async def cancel_action(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик для отмены действия по амнистии пользователя и возвращения в меню
    """
    await callback.answer()

    text = "❌️ Действие отменено!"
    await callback.message.edit_text(
        text=text,
        reply_markup=amnesty_actions_ikb(),
    )
    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=AmnestyStates.waiting_action_select,
    )


@router.callback_query(
    AmnestyStates.waiting_chat_select,
    F.data.startswith("chat__"),
)
async def execute_amnesty_action(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Выполняет выбранное действие амнистии в указанном чате"""
    await callback.answer()

    data = await state.get_data()

    action = data.get("action")
    chat_id = callback.data.split("__")[1]
    chat_dtos = data.get("chat_dtos")

    violator = ViolatorData(
        id=data.get("id"),
        username=data.get("username"),
        tg_id=data.get("tg_id"),
    )

    if chat_id != "all" and chat_id.isdigit():
        chat_dtos = [chat for chat in chat_dtos if chat.id != chat_id]

    amnesty_dto = AmnestyUserDTO(
        admin_tgid=str(callback.from_user.id),
        admin_username=callback.from_user.username,
        violator_tgid=violator.tg_id,
        violator_username=violator.username,
        violator_id=violator.id,
        chat_dtos=chat_dtos,
    )

    if action == Dialog.AmnestyUser.UNBAN:
        unban_usecase: UnbanUserUseCase = container.resolve(UnbanUserUseCase)
        try:
            await unban_usecase.execute(dto=amnesty_dto)
        except AmnestyError as e:
            logger.error("Ошибка амнистии: %s", e, exc_info=True)
            await callback.message.edit_text(
                text=e.get_user_message(),
                reply_markup=moderation_menu_ikb(),
            )
            return

        text = (
            f"✅ @{amnesty_dto.violator_username} полностью амнистирован!\n\n"
            "Все ограничения (бан, мут) сняты, а лестница наказаний обнулена."
        )
    elif action == Dialog.AmnestyUser.UNMUTE:
        unmute_usecase: UnmuteUserUseCase = container.resolve(UnmuteUserUseCase)
        try:
            await unmute_usecase.execute(dto=amnesty_dto)
        except AmnestyError as e:
            logger.error("Ошибка амнистии: %s", e, exc_info=True)
            await callback.message.edit_text(
                text=e.get_user_message(),
                reply_markup=moderation_menu_ikb(),
            )
            return

        text = (
            f"✅ @{amnesty_dto.violator_username} размучен!\n\n"
            "❗Все предыдущие предупреждения для пользователя сохранены."
        )
    elif action == Dialog.AmnestyUser.CANCEL_WARN:
        cancel_warn_usecase: CancelLastWarnUseCase = container.resolve(
            CancelLastWarnUseCase
        )
        try:
            result = await cancel_warn_usecase.execute(dto=amnesty_dto)
        except AmnestyError as e:
            logger.error("Ошибка отмены предупреждения: %s", e, exc_info=True)
            await callback.message.edit_text(
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

            text = (
                f"✅ <b>Последнее предупреждение отменено!</b>\n\n"
                f"Текущее количество предупреждений: <b>{result.current_warns_count}</b>\n"
                f"Следующий /warn для @{amnesty_dto.violator_username} приведёт к: <b>{next_step}</b>"
            )
        else:
            text = (
                f"✅ <b>Последнее предупреждение отменено во всех чатах!</b>\n\n"
                f"Обработано чатов: <b>{len(amnesty_dto.chat_dtos)}</b>\n"
                f"Пользователь: @{amnesty_dto.violator_username}"
            )
    else:
        text = "❗️Неизвестное действие. Попробуйте еще раз."
        await callback.message.edit_text(text=text, reply_markup=moderation_menu_ikb())
        return

    await callback.message.edit_text(
        text=text,
        reply_markup=amnesty_actions_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=AmnestyStates.waiting_action_select,
    )


@dataclass(frozen=True, slots=True)
class ViolatorData:
    id: int
    username: str
    tg_id: int


async def extract_violator_data_from_state(state: FSMContext) -> ViolatorData:
    data = await state.get_data()
    return ViolatorData(
        id=data.get("id"),
        username=data.get("username"),
        tg_id=data.get("tg_id"),
    )


async def handle_chats_error(
    callback: types.CallbackQuery,
    state: FSMContext,
    violator_username: str,
    error: Exception = None,
) -> None:
    """Обрабатывает ошибки получения чатов."""
    if error:
        logger.error("Ошибка получения чатов: %s", error, exc_info=True)
        text = "❌️ Произошла ошибка при получении списка чатов. Попробуйте еще раз."
    else:
        text = (
            f"❌️ Мы не нашли чатов, где @{violator_username} получил ограничение. "
            "Перепроверьте введённые данные, либо попробуйте снять ограничение вручную."
        )

    await callback.message.edit_text(text=text, reply_markup=moderation_menu_ikb())
    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=ModerationStates.menu,
    )


ACTION_CONFIG = {
    Dialog.AmnestyUser.UNBAN: {
        "usecase": GetChatsWithAnyRestrictionUseCase,
        "text": lambda username: f"Выберите чат, где нужно произвести полную амнистию для @{username}",
    },
    Dialog.AmnestyUser.UNMUTE: {
        "usecase": GetChatsWithMutedUserUseCase,
        "text": lambda username: f"Выберите чат, где нужно произвести размут @{username}",
    },
    Dialog.AmnestyUser.CANCEL_WARN: {
        "usecase": GetChatsWithPunishedUserUseCase,
        "text": lambda username: f"Выберите чат, где нужно отменить последнее предупреждение для @{username}",
    },
}
