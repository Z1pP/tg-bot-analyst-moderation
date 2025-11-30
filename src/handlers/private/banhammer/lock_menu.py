import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog
from constants.i18n import DEFAULT_LANGUAGE
from container import container
from keyboards.inline.menu import admin_menu_ikb
from services.user import UserService
from states import MenuStates
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.callback_query(F.data == "back_to_main_menu_from_block")
async def back_to_main_menu_from_block_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата в главное меню из меню блокировок"""
    await callback.answer()
    await state.clear()

    username = callback.from_user.first_name
    menu_text = Dialog.Menu.MENU_TEXT.format(username=username)

    # Получаем язык пользователя из БД
    user_service: UserService = container.resolve(UserService)
    db_user = await user_service.get_user(tg_id=str(callback.from_user.id))
    user_language = (
        db_user.language if db_user and db_user.language else DEFAULT_LANGUAGE
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=menu_text,
        reply_markup=admin_menu_ikb(
            user_language=user_language,
            admin_tg_id=str(callback.from_user.id),
        ),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=MenuStates.main_menu,
    )
