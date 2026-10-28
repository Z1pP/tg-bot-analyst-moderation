"""Archive chat settings handlers."""

from __future__ import annotations

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext
from punq import Container

from constants import Dialog
from constants.callback import CallbackData
from dto import GetChatWithArchiveDTO
from keyboards.inline.chats import chats_menu_ikb
from usecases.archive import GetArchiveSettingsUseCase
from utils.send_message import safe_edit_callback_message

router = Router(name=__name__)


@router.callback_query(F.data == CallbackData.Chat.ARCHIVE_SETTING)
async def archive_channel_setting_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    container: Container,
) -> None:
    """Обработчик настроек архивного чата."""
    chat_id: int | None = await state.get_value("chat_id")

    if chat_id is None:
        await safe_edit_callback_message(
            callback=callback,
            text=Dialog.Chat.CHAT_NOT_SELECTED,
            reply_markup=chats_menu_ikb(),
        )
        return

    usecase: GetArchiveSettingsUseCase = container.resolve(GetArchiveSettingsUseCase)
    result = await usecase.execute(GetChatWithArchiveDTO(chat_id=chat_id))

    await safe_edit_callback_message(
        callback=callback,
        text=result.text,
        reply_markup=result.reply_markup,
    )
