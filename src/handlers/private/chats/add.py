import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from constants import Dialog
from constants.callback import CallbackData
from keyboards.inline.chats import back_to_chats_menu_ikb

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Chat.ADD)
async def add_chat_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """
    Хендлер для команды добавления чата через callback.
    """
    await callback.answer()

    logger.info(
        "Пользователь %s начал добавление чата в отслеживание",
        callback.from_user.username,
    )

    await callback.message.edit_text(
        text=Dialog.Chat.ADD_CHAT_INSTRUCTION,
        reply_markup=back_to_chats_menu_ikb(),
    )
