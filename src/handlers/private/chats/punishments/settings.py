import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import chats_menu_ikb
from keyboards.inline.punishments import punishment_setting_ikb
from usecases.punishment import GetPunishmentLadderUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.PUNISHMENT_SETTING)
async def punishment_settings_handler(
    callback: CallbackQuery,
    state: FSMContext,
    container: Container,
):
    """Меню настройки наказаний"""
    await callback.answer()

    data = await state.get_data()
    chat_id = data.get("chat_id")

    if not chat_id:
        logger.error("chat_db_id не найден в state")
        await safe_edit_message(
            bot=callback.bot,
            chat_id=callback.message.chat.id,
            message_id=callback.message.message_id,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chats_menu_ikb(),
        )
        return

    usecase: GetPunishmentLadderUseCase = container.resolve(GetPunishmentLadderUseCase)
    result = await usecase.execute(chat_id=chat_id)

    if (
        result.formatted_text
        and result.formatted_text != Dialog.Punishment.LADDER_EMPTY
    ):
        ladder_heading = "🪜 Текущая лестница:"
        ladder_text = result.formatted_text
    else:
        ladder_heading = "🪜 Текущая лестница (по умолчанию):"
        ladder_text = Dialog.Punishment._DEFAULT_LADDER_LIST

    text = (
        "<b>⚙️ Настройка системы наказаний</b>\n\n"
        "В этом меню Вы можете настроить лестницу наказаний в чате.\n\n"
        f"{ladder_heading}\n\n{ladder_text}\n\n"
        f"{Dialog.Punishment.PUNISHMENT_STEP_INSTRUCTION}"
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=punishment_setting_ikb(),
    )
