from aiogram import F, Router, types
from aiogram.fsm.context import FSMContext

from keyboards.inline.templates import templates_menu_ikb
from states.templates import TemplateStateManager

router = Router(name=__name__)


@router.callback_query(F.data == "templates_menu")
async def back_to_templates_menu_handler(
    callback: types.CallbackQuery, state: FSMContext
):
    await callback.answer()

    await callback.message.edit_text(
        text="Выбери действие:",
        reply_markup=templates_menu_ikb(),
    )

    await state.set_state(TemplateStateManager.templates_menu)
