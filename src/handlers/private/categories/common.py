import logging

from aiogram import Bot, F, Router, types
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from punq import Container

from exceptions.category import CategoryNotFoundError
from keyboards.inline.categories import (
    cancel_category_ikb,
    confirmation_add_category_ikb,
    confirmation_edit_category_ikb,
)
from keyboards.inline.templates import templates_menu_ikb
from states import CategoryStateManager, TemplateStateManager
from usecases.categories import GetCategoryByIdUseCase
from utils.send_message import safe_edit_message

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith(("add_category", "edit_category__")))
async def request_category_name_handler(
    callback: CallbackQuery, state: FSMContext, container: Container
):
    await callback.answer()

    if callback.data.startswith("add_category"):
        mode = "add"
        category_id = None
        old_name = None
        text = "Отправьте название новой категории:"
        reply_markup = cancel_category_ikb()
    else:
        try:
            category_id = int(callback.data.split("__")[1])
        except (IndexError, ValueError):
            logger.warning("Некорректный формат callback_data: %s", callback.data)
            return await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text="⚠️ Некорректный запрос. Повторите действие через меню.",
                reply_markup=templates_menu_ikb(),
            )
        mode = "edit"
        old_name = None
        try:
            usecase: GetCategoryByIdUseCase = container.resolve(GetCategoryByIdUseCase)
            category = await usecase.execute(category_id)
            old_name = category.name
        except CategoryNotFoundError as e:
            logger.warning("Категория ID=%d не найдена: %s", category_id, e)
            return await safe_edit_message(
                bot=callback.bot,
                chat_id=callback.message.chat.id,
                message_id=callback.message.message_id,
                text=e.get_user_message(),
            )
        text = f"<b>Редактирование категории:</b> {old_name}\n\nВведите новое название:"
        reply_markup = cancel_category_ikb()

    await state.update_data(
        mode=mode,
        category_id=category_id,
        old_name=old_name,
        active_message_id=callback.message.message_id,
    )

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=reply_markup,
    )

    await state.set_state(CategoryStateManager.process_category_name)


@router.message(CategoryStateManager.process_category_name)
async def process_category_name_handler(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
):
    data = await state.get_data()
    active_message_id = data.get("active_message_id")
    mode = data.get("mode", "add")

    if not message.text:
        if active_message_id:
            await safe_edit_message(
                bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text="❗Отправьте название текстом (без медиа).",
                reply_markup=cancel_category_ikb(),
            )
        return

    category_name = message.text.strip()
    await message.delete()

    if not validate_category_name(category_name):
        if active_message_id:
            await safe_edit_message(
                bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text="❗Название должно содержать от 3 до 50 символов.",
                reply_markup=cancel_category_ikb(),
            )
        return

    await state.update_data(category_name=category_name)

    text = f"Категория <b>{category_name}</b>.\nВы подтверждаете "
    text += "создание категории?" if mode == "add" else "изменение категории?"

    if active_message_id:
        await safe_edit_message(
            bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=text,
            reply_markup=confirmation_add_category_ikb()
            if mode == "add"
            else confirmation_edit_category_ikb(),
        )

    await state.set_state(
        CategoryStateManager.confirm_category_creation
        if mode == "add"
        else CategoryStateManager.confirm_category_edit
    )


@router.callback_query(F.data == "cancel_category")
async def cancel_category_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="❌ Действие отменено.",
        reply_markup=templates_menu_ikb(),
    )
    await state.set_state(TemplateStateManager.templates_menu)


def validate_category_name(category_name: str) -> bool:
    """Валидирует название категории"""
    return 3 <= len(category_name) <= 50
