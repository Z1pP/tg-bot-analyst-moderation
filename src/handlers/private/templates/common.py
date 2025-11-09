from aiogram import types
from aiogram.fsm.context import FSMContext

from states.templates import TemplateStateManager
from utils.state_logger import log_and_set_state


async def common_process_template_title_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
):
    await callback.answer()

    await state.update_data(title=callback.data)

    await callback.message.edit_text(
        text=f"Отправьте контент для шаблона '{callback.data}' (текст, фото или медиагруппу):",
        reply_markup=None,
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=TemplateStateManager.process_template_content,
    )
