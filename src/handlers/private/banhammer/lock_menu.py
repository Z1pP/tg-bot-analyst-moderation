import logging

from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from constants import Dialog, KbCommands
from keyboards.inline.banhammer import block_actions_ikb
from keyboards.reply.menu import admin_menu_kb
from states import BanHammerStates, MenuStates
from utils.state_logger import log_and_set_state

logger = logging.getLogger(__name__)
router = Router(name=__name__)


@router.message(F.text == KbCommands.LOCK_MENU)
async def lock_menu_handler(message: types.Message, state: FSMContext) -> None:
    """
    Обработчик отвечающий за вывод настроек блокировки.
    """
    # Удаляем исходное сообщение
    try:
        await message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение: {e}")

    await log_and_set_state(
        message=message,
        state=state,
        new_state=BanHammerStates.block_menu,
    )

    await message.answer(
        text=Dialog.BlockMenu.SELECT_ACTION,
        reply_markup=block_actions_ikb(),
    )


@router.callback_query(F.data == "back_to_main_menu_from_block")
async def back_to_main_menu_from_block_handler(
    callback: types.CallbackQuery, state: FSMContext
) -> None:
    """Обработчик возврата в главное меню из меню блокировок"""
    await callback.answer()
    await state.clear()

    username = callback.from_user.first_name
    menu_text = Dialog.MENU_TEXT.format(username=username)

    await callback.message.answer(
        text=menu_text,
        reply_markup=admin_menu_kb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=MenuStates.main_menu,
    )

    try:
        await callback.message.delete()
    except Exception as e:
        logger.warning(f"Не удалось удалить сообщение меню блокировок: {e}")
