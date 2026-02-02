import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.punishments import (
    cancel_punishment_creation_ikb,
    punishment_action_ikb,
    punishment_next_step_ikb,
)
from mappers.punishment_mapper import map_temp_ladder_to_update_dto
from states import ChatStateManager, PunishmentState
from usecases.punishment import (
    UpdatePunishmentLadderUseCase,
)
from utils.data_parser import parse_duration
from utils.formatter import format_duration
from utils.send_message import safe_edit_message

from .settings import punishment_settings_handler

router = Router(name=__name__)
logger = logging.getLogger(__name__)


def _step_to_emoji(step: int) -> str:
    """Return step number formatted with emoji digits."""
    digit_map = {
        "0": "0️⃣",
        "1": "1️⃣",
        "2": "2️⃣",
        "3": "3️⃣",
        "4": "4️⃣",
        "5": "5️⃣",
        "6": "6️⃣",
        "7": "7️⃣",
        "8": "8️⃣",
        "9": "9️⃣",
    }
    return "".join(digit_map.get(ch, ch) for ch in str(step))


@router.callback_query(F.data == CallbackData.Chat.PUNISHMENT_CREATE_NEW)
async def start_create_ladder_handler(callback: CallbackQuery, state: FSMContext):
    """Начало создания новой лестницы"""
    await callback.answer()

    await state.update_data(
        temp_ladder=[], current_step=1, active_message_id=callback.message.message_id
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Punishment.STEP_SELECT_ACTION.format(step_emoji=_step_to_emoji(1)),
        reply_markup=punishment_action_ikb(),
    )
    await state.set_state(PunishmentState.waiting_for_action_type)


@router.callback_query(
    PunishmentState.waiting_for_action_type,
    F.data.startswith(CallbackData.Chat.PREFIX_PUNISH_ACTION),
)
async def process_action_type_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
):
    """Обработка выбора типа наказания для ступени"""
    await callback.answer()

    action = callback.data.split("_")[-1]

    if action == "cancel":
        await punishment_settings_handler(
            callback=callback,
            state=state,
            container=container,
        )
        return

    if action == "mute":
        await state.set_state(PunishmentState.waiting_for_duration)
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Punishment.ENTER_MUTE_DURATION,
            reply_markup=cancel_punishment_creation_ikb(),
        )
    else:
        # Преобразуем warn -> WARNING, ban -> BAN
        p_type = "WARNING" if action in ["warn", "warning"] else action.upper()
        await add_step_to_temp_ladder(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            state=state,
            action=p_type,
        )


@router.message(PunishmentState.waiting_for_duration)
async def process_mute_duration_handler(message: Message, state: FSMContext):
    """Обработка ввода длительности мута"""
    data = await state.get_data()
    active_message_id = data.get("active_message_id")

    duration = parse_duration(message.text)

    if duration is None:
        if active_message_id:
            await safe_edit_message(
                bot=message.bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=Dialog.Punishment.INVALID_DURATION_FORMAT
                + "\n\n"
                + Dialog.Punishment.ENTER_MUTE_DURATION,
                reply_markup=cancel_punishment_creation_ikb(),
            )
        await message.delete()
        return

    await message.delete()

    if active_message_id:
        await add_step_to_temp_ladder(
            bot=message.bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            state=state,
            action="MUTE",
            duration=duration,
        )


async def add_step_to_temp_ladder(
    bot: Bot,
    chat_id: int,
    message_id: int,
    state: FSMContext,
    action: str,
    duration: int = None,
):
    """Вспомогательная функция для добавления ступени в список"""
    data = await state.get_data()
    temp_ladder = data.get("temp_ladder", [])
    current_step = data.get("current_step", 1)

    temp_ladder.append(
        {"step": current_step, "punishment_type": action, "duration_seconds": duration}
    )

    await state.update_data(temp_ladder=temp_ladder, current_step=current_step + 1)

    if action == "MUTE" and duration:
        action_ru = f"Мут {format_duration(duration)}"
    else:
        action_ru = {"WARNING": "Предупреждение", "MUTE": "Мут", "BAN": "Бан"}.get(
            action, action
        )

    text = Dialog.Punishment.STEP_ACTION_SAVED.format(
        step_emoji=_step_to_emoji(current_step),
        action=action_ru,
    )

    await safe_edit_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=punishment_next_step_ikb(),
    )
    await state.set_state(PunishmentState.confirm_save)


@router.callback_query(
    PunishmentState.confirm_save,
    F.data == CallbackData.Chat.PUNISH_STEP_NEXT,
)
async def next_step_handler(callback: CallbackQuery, state: FSMContext):
    """Переход к следующей ступени"""
    await callback.answer()
    data = await state.get_data()
    step = data.get("current_step", 1)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Punishment.STEP_SELECT_ACTION.format(
            step_emoji=_step_to_emoji(step)
        ),
        reply_markup=punishment_action_ikb(),
    )
    await state.set_state(PunishmentState.waiting_for_action_type)


@router.callback_query(
    PunishmentState.confirm_save,
    F.data == CallbackData.Chat.PUNISH_STEP_SAVE,
)
async def save_ladder_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
):
    """Сохранение всей лестницы в БД"""
    data = await state.get_data()
    chat_db_id = data.get("chat_id")
    temp_ladder = data.get("temp_ladder", [])

    if not chat_db_id:
        await callback.answer("Ошибка: чат не выбран", show_alert=True)
        return

    try:
        dto = map_temp_ladder_to_update_dto(
            chat_db_id=chat_db_id, temp_ladder=temp_ladder
        )

        usecase = container.resolve(UpdatePunishmentLadderUseCase)
        result = await usecase.execute(dto=dto, admin_tg_id=str(callback.from_user.id))

        if result.success:
            await callback.answer(Dialog.Punishment.LADDER_SAVED)
            await state.set_state(ChatStateManager.selecting_chat)
            await punishment_settings_handler(
                callback=callback, state=state, container=container
            )
        else:
            await callback.answer(
                result.error_message or Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED
            )
    except Exception as e:
        logger.error("Error saving punishment ladder: %s", e)
        await callback.answer(Dialog.Punishment.LADDER_SAVE_ERROR, show_alert=True)


@router.callback_query(F.data == CallbackData.Chat.PUNISH_STEP_CANCEL)
async def cancel_creation_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
):
    """Отмена создания"""
    await callback.answer()
    await state.set_state(ChatStateManager.selecting_chat)
    await punishment_settings_handler(
        callback=callback, state=state, container=container
    )
