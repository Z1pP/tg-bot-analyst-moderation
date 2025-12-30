import logging

from aiogram import Bot, F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from constants import Dialog
from constants.callback import CallbackData
from container import container
from keyboards.inline.chats import chat_actions_ikb
from keyboards.inline.punishments import (
    punishment_action_ikb,
    punishment_next_step_ikb,
    punishment_setting_ikb,
)
from mappers.punishment_mapper import map_temp_ladder_to_update_dto
from states import ChatStateManager, PunishmentState
from usecases.punishment import (
    GetPunishmentLadderUseCase,
    SetDefaultPunishmentLadderUseCase,
    UpdatePunishmentLadderUseCase,
)
from utils.data_parser import parse_duration
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.PUNISHMENT_SETTING)
async def punishment_setting_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Меню настройки наказаний"""
    await callback.answer()

    data = await state.get_data()
    chat_db_id = data.get("chat_id")
    if not chat_db_id:
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chat_actions_ikb(),
        )
        return

    usecase = container.resolve(GetPunishmentLadderUseCase)
    result = await usecase.execute(chat_db_id=chat_db_id)

    text = Dialog.Punishment.PUNISHMENT_SETTING_MENU.format(
        ladder_text=result.formatted_text
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=punishment_setting_ikb(),
    )


@router.callback_query(F.data == CallbackData.Chat.PUNISHMENT_SET_DEFAULT)
async def set_default_punishments_handler(
    callback: CallbackQuery,
    state: FSMContext,
):
    """Сброс до настроек по умолчанию"""
    data = await state.get_data()
    chat_db_id = data.get("chat_id")
    if not chat_db_id:
        await callback.answer(Dialog.Chat.CHAT_NOT_SELECTED)
        return

    try:
        usecase = container.resolve(SetDefaultPunishmentLadderUseCase)
        result = await usecase.execute(chat_db_id=chat_db_id)
        if result.success:
            await callback.answer(Dialog.Punishment.SUCCESS_SET_DEFAULT)
            await punishment_setting_handler(callback, state)
        else:
            await callback.answer(
                result.error_message or Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED
            )
    except Exception as e:
        logger.error("Error setting default punishments: %s", e)
        await callback.answer(Dialog.Punishment.ERROR_SET_DEFAULT, show_alert=True)


# --- Creation Flow ---


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
        text=Dialog.Punishment.CREATE_STEP_TITLE.format(step=1),
        reply_markup=punishment_action_ikb(),
    )
    await state.set_state(PunishmentState.waiting_for_action_type)


@router.callback_query(
    PunishmentState.waiting_for_action_type, F.data.startswith("punish_action_")
)
async def process_action_type_handler(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора типа наказания для ступени"""
    action = callback.data.split("_")[-1]

    if action == "cancel":
        await state.set_state(ChatStateManager.selecting_chat)
        await punishment_setting_handler(callback, state)
        return

    await callback.answer()

    if action == "mute":
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Punishment.ENTER_MUTE_DURATION,
        )
        await state.set_state(PunishmentState.waiting_for_duration)
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

    action_ru = {"WARNING": "Предупреждение", "MUTE": "Мут", "BAN": "Бан"}.get(
        action, action
    )

    text = Dialog.Punishment.STEP_ADDED.format(step=current_step, action=action_ru)

    await safe_edit_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
        text=text,
        reply_markup=punishment_next_step_ikb(),
    )
    await state.set_state(PunishmentState.confirm_save)


@router.callback_query(PunishmentState.confirm_save, F.data == "punish_step_next")
async def next_step_handler(callback: CallbackQuery, state: FSMContext):
    """Переход к следующей ступени"""
    await callback.answer()
    data = await state.get_data()
    step = data.get("current_step", 1)

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=Dialog.Punishment.CREATE_STEP_TITLE.format(step=step),
        reply_markup=punishment_action_ikb(),
    )
    await state.set_state(PunishmentState.waiting_for_action_type)


@router.callback_query(PunishmentState.confirm_save, F.data == "punish_step_save")
async def save_ladder_handler(
    callback: CallbackQuery,
    state: FSMContext,
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
        result = await usecase.execute(dto=dto)

        if result.success:
            await callback.answer(Dialog.Punishment.LADDER_SAVED)
            await state.set_state(ChatStateManager.selecting_chat)
            await punishment_setting_handler(callback, state)
        else:
            await callback.answer(
                result.error_message or Dialog.Chat.CHAT_NOT_FOUND_OR_ALREADY_REMOVED
            )
    except Exception as e:
        logger.error("Error saving punishment ladder: %s", e)
        await callback.answer(Dialog.Punishment.LADDER_SAVE_ERROR, show_alert=True)


@router.callback_query(F.data == "punish_step_cancel")
async def cancel_creation_handler(callback: CallbackQuery, state: FSMContext):
    """Отмена создания"""
    await callback.answer()
    await state.set_state(ChatStateManager.selecting_chat)
    await punishment_setting_handler(callback, state)
