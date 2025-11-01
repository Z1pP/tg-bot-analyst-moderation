from dataclasses import dataclass
import logging

from aiogram import F, Bot, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from constants import KbCommands, InlineButtons, Dialog
from constants.punishment import PunishmentType
from container import container
from dto import AmnestyUserDTO
from exceptions import AmnestyError
from keyboards.inline.chats_kb import tracked_chats_with_all_kb
from keyboards.inline.amnesty import confirm_action_ikb
from keyboards.inline.banhammer import amnesty_actions_ikb, block_actions_ikb
from services import UserService
from states import AmnestyStates, BanHammerStates
from usecases.amnesty import (
    CancelLastWarnUseCase,
    GetChatsWithBannedUserUseCase,
    GetChatsWithMutedUserUseCase,
    GetChatsWithPunishedUserUseCase,
    UnbanUserUseCase,
    UnmuteUserUseCase,
)
from utils.state_logger import log_and_set_state
from utils.user_data_parser import parse_data_from_text
from utils.formatter import format_duration


router = Router()
logger = logging.getLogger(__name__)
block_buttons = InlineButtons.BlockButtons()


@router.callback_query(
    F.data == block_buttons.AMNESTY,
    BanHammerStates.block_menu,
)
async def amnesty_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик отвечающий за действия по амнистии пользователя в чате.
    """
    await callback.answer()
    await state.update_data(message_to_edit_id=callback.message.message_id)

    await callback.message.edit_text(text=Dialog.AmnestyUser.INPUT_USER_DATA)
    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=AmnestyStates.waiting_user_input,
    )


@router.message(AmnestyStates.waiting_user_input, F.text)
async def waiting_user_data_input(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """
    Обработчик для обработки введенной информации о пользователе
    """
    user_data = parse_data_from_text(text=message.text)

    await message.delete()

    data = await state.get_data()
    message_to_edit_id = data.get("message_to_edit_id")

    if user_data is None:
        await bot.edit_message_text(
            text=Dialog.Error.INVALID_USERNAME_FORMAT,
            chat_id=message.chat.id,
            message_id=message_to_edit_id,
            reply_markup=block_actions_ikb(),
        )
        await log_and_set_state(
            message=message,
            state=state,
            new_state=BanHammerStates.block_menu,
        )
        return

    user_service: UserService = container.resolve(UserService)

    user = None

    if user_data.tg_id:
        user = await user_service.get_user(tg_id=user_data.tg_id)
    elif user_data.username:
        user = await user_service.get_by_username(username=user_data.username)

    if user is None:
        identificator = (
            f"<code>{user_data.tg_id}</code>"
            if user_data.tg_id
            else f"<b>@{user_data.username}</b>"
        )
        await bot.edit_message_text(
            text=Dialog.BanUser.USER_NOT_FOUND.format(
                identificator=identificator,
            ),
            chat_id=message.chat.id,
            message_id=message_to_edit_id,
            reply_markup=block_actions_ikb(),
        )
        await log_and_set_state(
            message=message,
            state=state,
            new_state=BanHammerStates.block_menu,
        )
        return

    await state.update_data(
        username=user.username,
        id=user.id,
        tg_id=user.tg_id,
    )

    if message_to_edit_id:
        try:
            await bot.edit_message_text(
                text=Dialog.AmnestyUser.SELECT_ACTION.format(
                    username=user.username,
                    tg_id=user.tg_id,
                ),
                chat_id=message.chat.id,
                message_id=message_to_edit_id,
                reply_markup=amnesty_actions_ikb(),
            )
        except TelegramBadRequest as e:
            logger.error("Ошибка редактирования сообщения: %s", e, exc_info=True)

    await log_and_set_state(
        message=message,
        state=state,
        new_state=AmnestyStates.waiting_action_select,
    )


@router.callback_query(
    F.data == block_buttons.UNBAN,
    AmnestyStates.waiting_action_select,
)
async def unban_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обработчик для разблокирования пользователя в чате"""
    await callback.answer()

    violator = await extract_violator_data_from_state(state=state)

    await state.update_data(action=block_buttons.UNBAN)

    await callback.message.edit_text(
        text=Dialog.AmnestyUser.UNBAN_CONFIRMATION.format(username=violator.username),
        reply_markup=confirm_action_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=AmnestyStates.waiting_confirmation_action,
    )


@router.callback_query(
    F.data == block_buttons.UNMUTE,
    AmnestyStates.waiting_action_select,
)
async def unmute_warn_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обработчик для отмены мута в чате с сохранением текущего предупреждения"""
    await callback.answer()

    violator = await extract_violator_data_from_state(state=state)

    await state.update_data(action=block_buttons.UNMUTE)

    await callback.message.edit_text(
        text=Dialog.AmnestyUser.UNMUTE_CONFIRMATION.format(username=violator.username),
        reply_markup=confirm_action_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=AmnestyStates.waiting_confirmation_action,
    )


@router.callback_query(
    F.data == block_buttons.CANCEL_WARN,
    AmnestyStates.waiting_action_select,
)
async def cancel_warn_handler(callback: types.CallbackQuery, state: FSMContext) -> None:
    """Обработчик для отмены (удаления) прошлого предупреждения"""
    await callback.answer()

    violator = await extract_violator_data_from_state(state=state)

    await state.update_data(action=block_buttons.CANCEL_WARN)

    await callback.message.edit_text(
        text=Dialog.AmnestyUser.CANCEL_WARN_CONFIRMATION.format(
            username=violator.username
        ),
        reply_markup=confirm_action_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=AmnestyStates.waiting_confirmation_action,
    )


@router.callback_query(
    F.data == block_buttons.BACK_TO_BLOCK_MENU,
    AmnestyStates.waiting_action_select,
)
async def back_to_block_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Обработчик для возврата в меню блокировок"""

    await callback.answer()

    await callback.message.edit_text(
        text=Dialog.BlockMenu.SELECT_ACTION,
        reply_markup=block_actions_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=BanHammerStates.block_menu,
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
            reply_markup=block_actions_ikb(),
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
        reply_markup=tracked_chats_with_all_kb(dtos=chat_dtos),
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

    if action == KbCommands.UNBAN:
        unban_usecase: UnbanUserUseCase = container.resolve(UnbanUserUseCase)
        try:
            await unban_usecase.execute(dto=amnesty_dto)
        except AmnestyError as e:
            logger.error("Ошибка амнистии: %s", e, exc_info=True)
            await callback.message.edit_text(
                text=e.get_user_message(),
                reply_markup=block_actions_ikb(),
            )
            return

        text = (
            f"✅ @{amnesty_dto.violator_username} амнистирован — "
            "все предупреждения были сброшены!"
        )
    elif action == KbCommands.UNMUTE:
        unmute_usecase: UnmuteUserUseCase = container.resolve(UnmuteUserUseCase)
        try:
            await unmute_usecase.execute(dto=amnesty_dto)
        except AmnestyError as e:
            logger.error("Ошибка амнистии: %s", e, exc_info=True)
            await callback.message.edit_text(
                text=e.get_user_message(),
                reply_markup=block_actions_ikb(),
            )
            return

        text = (
            f"✅ @{amnesty_dto.violator_username} размучен!\n\n"
            "❗Все предыдущие предупреждения для пользователя сохранены."
        )
    elif action == KbCommands.CANCEL_WARN:
        cancel_warn_usecase: CancelLastWarnUseCase = container.resolve(
            CancelLastWarnUseCase
        )
        try:
            result = await cancel_warn_usecase.execute(dto=amnesty_dto)
        except AmnestyError as e:
            logger.error("Ошибка отмены предупреждения: %s", e, exc_info=True)
            await callback.message.edit_text(
                text=e.get_user_message(),
                reply_markup=block_actions_ikb(),
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
        await callback.message.edit_text(text=text, reply_markup=block_actions_ikb())
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

    await callback.message.edit_text(text=text, reply_markup=block_actions_ikb())
    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=BanHammerStates.block_menu,
    )


ACTION_CONFIG = {
    KbCommands.UNBAN: {
        "usecase": GetChatsWithBannedUserUseCase,
        "text": lambda username: f"Выберите чат, где нужно произвести амнистию @{username}",
    },
    KbCommands.UNMUTE: {
        "usecase": GetChatsWithMutedUserUseCase,
        "text": lambda username: f"Выберите чат, где нужно произвести размут @{username}",
    },
    KbCommands.CANCEL_WARN: {
        "usecase": GetChatsWithPunishedUserUseCase,
        "text": lambda username: f"Выберите чат, где нужно отменить последнее предупреждение для @{username}",
    },
}
