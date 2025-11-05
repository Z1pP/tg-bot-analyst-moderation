from aiogram import F, Router, types

from keyboards.inline.templates import templates_menu_ikb

router = Router(name=__name__)


@router.callback_query(F.data == "templates_menu")
async def templates_menu_handler(callback: types.CallbackQuery):
    """Обработчик меню шаблонов"""
    await callback.answer()

    message_text = "Выбери действие:"

    await callback.message.edit_text(
        text=message_text,
        reply_markup=templates_menu_ikb(),
    )
