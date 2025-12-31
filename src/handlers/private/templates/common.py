from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext

from keyboards.inline.templates import cancel_template_ikb, templates_menu_ikb
from states.templates import TemplateStateManager
from utils.send_message import safe_edit_message

router = Router(name=__name__)


async def common_process_template_title_handler(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()
    active_message_id = data.get("active_message_id")

    template_title = message.text.strip()

    await message.delete()

    if not validate_template_title(template_title):
        if active_message_id:
            await safe_edit_message(
                bot=bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text="❗Название должно содержать от 3 до 50 символов.",
                reply_markup=cancel_template_handler(),
            )
            return

    await state.update_data(title=template_title)

    await safe_edit_message(
        bot=bot,
        chat_id=message.chat.id,
        message_id=active_message_id,
        text=f"Отправьте контент для шаблона '{template_title}' (текст, фото или медиагруппу):",
        reply_markup=cancel_template_ikb(),
    )

    await state.set_state(TemplateStateManager.process_template_content)


@router.callback_query(F.data == "cancel_template")
async def cancel_template_handler(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="❌ Действие отменено.",
        reply_markup=templates_menu_ikb(),
    )
    await state.set_state(TemplateStateManager.templates_menu)


def validate_template_title(title: str) -> bool:
    """Валидирует название шаблона"""
    return 3 <= len(title) <= 50
