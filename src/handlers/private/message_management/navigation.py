import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants.callback import CallbackData

from .helpers import show_message_management_menu

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data == CallbackData.Messages.SHOW_MENU)
async def message_management_menu_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
) -> None:
    """Показывает главное меню управления сообщениями (ввод ссылки).

    Args:
        callback: Объект callback-запроса.
        state: Контекст состояния FSM.
    """
    await callback.answer()

    logger.info(
        "Администратор %s выбрал пункт управления сообщениями",
        callback.from_user.username,
    )

    await show_message_management_menu(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        state=state,
    )
