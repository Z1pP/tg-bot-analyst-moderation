from aiogram import F, Router, types

from keyboards.reply.menu import tamplates_menu_kb
from utils.send_message import send_html_message_with_kb

router = Router(name=__name__)


@router.callback_query(F.data == "templates_menu")
async def templates_menu_handler(callback: types.Message):
    """Обработчик меню шаблонов"""
    await callback.answer()

    message_text = "Выбери действие:"

    await send_html_message_with_kb(
        message=callback.message,
        text=message_text,
        reply_markup=tamplates_menu_kb(),
    )
