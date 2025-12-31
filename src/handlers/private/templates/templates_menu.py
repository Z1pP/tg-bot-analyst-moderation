from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from keyboards.inline.templates import templates_menu_ikb
from states import TemplateStateManager

router = Router(name=__name__)


@router.callback_query(F.data == "templates_menu")
async def templates_menu_handler(callback: types.CallbackQuery, state: FSMContext):
    """Обработчик меню шаблонов"""
    await callback.answer()
    await state.clear()

    message_text = "Выбери действие:"

    await callback.message.edit_text(
        text=message_text,
        reply_markup=templates_menu_ikb(),
    )

    await state.set_state(TemplateStateManager.templates_menu)
