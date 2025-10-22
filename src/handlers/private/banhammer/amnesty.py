from dataclasses import dataclass
import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import KbCommands
from constants.punishment import PunishmentType
from container import container
from dto import AmnestyUserDTO
from exceptions import AmnestyError
from keyboards.inline.chats_kb import tracked_chats_with_all_kb
from keyboards.reply import admin_menu_kb, amnesty_actions_kb
from keyboards.inline.amnesty import confirm_action_ikb
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


@router.message(
    F.text == KbCommands.AMNESTY,
    BanHammerStates.block_menu,
)
async def amnesty_handler(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик отвечающий за действия по амнистии пользователя в чате.
    """
    text = (
        "🕊️ <b>Амнистия пользователя</b>\n\n"
        "Для разблокировки или снятия ограничения пришлите @username или Telegram ID пользователя\n\n"
        "<i>Пример: @john_pidor или <code>123456789</code></i>"
    )
    await message.reply(text=text)
    await log_and_set_state(
        message=message,
        state=state,
        new_state=AmnestyStates.waiting_user_input,
    )


@router.message(
    AmnestyStates.waiting_user_input,
)
async def waiting_user_data_input(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик для обработки введенной информации о пользователе
    """
    user_data = parse_data_from_text(text=message.text)

    if user_data is None:
        text = "❗Неверный формат ввода. Попробуйте еще раз."
        await message.reply(text=text)
        return

    user_service: UserService = container.resolve(UserService)

    user = None

    if user_data.tg_id:
        user = await user_service.get_user(tg_id=user_data.tg_id)
    elif user_data.username:
        user = await user_service.get_by_username(username=user_data.username)

    if user is None:
        text = "❗Пользователь не найден. Попробуйте еще раз."
        await message.reply(text=text)
        return

    await state.update_data(
        username=user.username,
        id=user.id,
        tg_id=user.tg_id,
    )

    text = f"Что делаем с <b>@{user.username}</b>?"

    await message.reply(text=text, reply_markup=amnesty_actions_kb())

    await log_and_set_state(
        message=message,
        state=state,
        new_state=AmnestyStates.waiting_action_select,
    )


@router.message(
    F.text == KbCommands.UNBAN,
    AmnestyStates.waiting_action_select,
)
async def unban_handler(message: types.Message, state: FSMContext) -> None:
    """Обработчик для разблокирования пользователя в чате"""

    violator = await extract_violator_data_from_state(state=state)

    text = (
        f"Полная разблокировка даст возможность @{violator.username} вернуться в чат — "
        "все предыдущие предупреждения будут сброшены.\n\n<b>Вы уверены, что хотите "
        f"полностью разблокировать @{violator.username}?</b>"
    )

    await state.update_data(action=KbCommands.UNBAN)

    await message.reply(text=text, reply_markup=confirm_action_ikb())

    await log_and_set_state(
        message=message,
        state=state,
        new_state=AmnestyStates.waiting_confirmation_action,
    )


@router.message(
    F.text == KbCommands.UNMUTE,
    AmnestyStates.waiting_action_select,
)
async def unmute_warn_handler(message: types.Message, state: FSMContext) -> None:
    """Обработчик для отмены мута в чате с сохранением текущего предупреждения"""

    violator = await extract_violator_data_from_state(state=state)

    text = (
        f"Размут даст возможность @{violator.username} писать в чате, однако "
        "предпреждения не будут сброшены.\n\nВы уверены, что хотите размутить "
        f"данного @{violator.username}?"
    )

    await state.update_data(action=KbCommands.UNMUTE)

    await message.reply(text=text, reply_markup=confirm_action_ikb())

    await log_and_set_state(
        message=message,
        state=state,
        new_state=AmnestyStates.waiting_confirmation_action,
    )


@router.message(
    F.text == KbCommands.CANCEL_WARN,
    AmnestyStates.waiting_action_select,
)
async def cancel_warn_handler(message: types.Message, state: FSMContext) -> None:
    """Обработчик для отмены (удаления) прошлого предупреждения"""

    violator = await extract_violator_data_from_state(state=state)

    text = (
        f"Отмена последнего предупреждения даст возможность @{violator.username} "
        "писать в чате.\n\n<b>Вы уверены, что хотите отменить последнее предупреждение "
        f"для @{violator.username}?</b>"
    )

    await state.update_data(action=KbCommands.CANCEL_WARN)

    await message.reply(text=text, reply_markup=confirm_action_ikb())

    await log_and_set_state(
        message=message,
        state=state,
        new_state=AmnestyStates.waiting_confirmation_action,
    )


@router.callback_query(
    F.data == "confirm_action",
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
        await callback.message.delete()
        await callback.message.answer(text=text, reply_markup=admin_menu_kb())
        await state.clear()
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
    F.data == "cancel_action",
    AmnestyStates.waiting_confirmation_action,
)
async def cancel_action(callback: types.CallbackQuery, state: FSMContext) -> None:
    """
    Обработчик для отмены действия по амнистии пользователя и возвращения в меню
    """
    await callback.answer()

    text = "❌️ Действие отменено!"

    await callback.message.delete()
    await callback.message.answer(text=text, reply_markup=admin_menu_kb())
    await state.clear()


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
            await callback.message.delete()
            await callback.message.answer(
                text=e.get_user_message(),
                reply_markup=admin_menu_kb(),
            )
            await state.clear()
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
            await callback.message.delete()
            await callback.message.answer(
                text=e.get_user_message(),
                reply_markup=admin_menu_kb(),
            )
            await state.clear()
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
            await callback.message.delete()
            await callback.message.answer(
                text=e.get_user_message(),
                reply_markup=admin_menu_kb(),
            )
            await state.clear()
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
        await callback.message.delete()
        await callback.message.answer(text=text, reply_markup=admin_menu_kb())
        await state.clear()
        return

    await callback.message.delete()
    await callback.message.answer(
        text=text,
        reply_markup=amnesty_actions_kb(),
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

    await callback.message.delete()
    await callback.message.answer(text=text, reply_markup=admin_menu_kb())
    await state.clear()


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
