import logging

from aiogram import Bot, F, Router, types
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext

from container import container
from dto import CreateCategoryDTO
from exceptions.caregory import CategoryAlreadyExists
from keyboards.inline.categories import (
    cancel_add_category_ikb,
    confirmation_add_category_ikb,
)
from keyboards.inline.templates import templates_menu_ikb
from states import CategoryStateManager, TemplateStateManager
from usecases.categories import CreateCategoryUseCase
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


async def safe_edit_message(
    bot: Bot,
    chat_id: int,
    message_id: int,
    text: str | None = None,
    reply_markup: types.InlineKeyboardMarkup | None = None,
) -> bool:
    """Безопасное редактирование сообщения с обработкой типичных ошибок Telegram"""
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=text,
            reply_markup=reply_markup,
        )
        return True

    except TelegramBadRequest as e:
        msg = (e.message or str(e)).lower()
        if "message is not modified" in msg:
            logger.debug("Сообщение %d не изменилось", message_id)
        elif "message to edit not found" in msg:
            logger.warning("Сообщение %d не найдено для редактирования", message_id)
        elif "message can't be edited" in msg:
            logger.warning("Сообщение %d больше нельзя редактировать", message_id)
        else:
            logger.error("Ошибка при редактировании сообщения: %s", e, exc_info=True)
        return False


@router.callback_query(
    F.data == "add_category",
    TemplateStateManager.templates_menu,
)
async def add_category_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Обработчик добавления новой категории"""
    await callback.answer()

    sent_success = await safe_edit_message(
        bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="Отправьте название новой категории:",
        reply_markup=cancel_add_category_ikb(),
    )

    if sent_success:
        await state.update_data(active_message_id=callback.message.message_id)

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=CategoryStateManager.process_category_name,
    )


@router.message(CategoryStateManager.process_category_name)
async def process_category_name_handler(
    message: types.Message,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Обработчик получения названия категории"""
    data = await state.get_data()
    active_message_id = data.get("active_message_id")

    # Проверяем формат ввода
    if not message.text:
        if active_message_id:
            await safe_edit_message(
                bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=(
                    "❗Недопустимый формат ввода данных.\n"
                    "Пожалуйста, отправьте название текстом (без фото, видео и т.д.)."
                ),
                reply_markup=cancel_add_category_ikb(),
            )
        return

    category_name = message.text.strip()
    await message.delete()

    # Валидация длины названия
    if not validate_category_name(category_name):
        if active_message_id:
            await safe_edit_message(
                bot,
                chat_id=message.chat.id,
                message_id=active_message_id,
                text=(
                    "❗Недопустимый формат ввода данных.\n"
                    "Название категории должно содержать от 3 до 50 символов."
                ),
                reply_markup=cancel_add_category_ikb(),
            )
        return

    # Подтверждение создания
    if active_message_id:
        await safe_edit_message(
            bot,
            chat_id=message.chat.id,
            message_id=active_message_id,
            text=(
                f"Категория <b>{category_name}</b>.\n"
                "Вы подтверждаете создание категории?"
            ),
            reply_markup=confirmation_add_category_ikb(),
        )

    await state.update_data(category_name=category_name)

    await log_and_set_state(
        message=message,
        state=state,
        new_state=CategoryStateManager.confirm_category_creation,
    )


@router.callback_query(
    F.data == "cancel_add_category",
)
async def cancel_category_creation_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Обработчик отмены создания категории"""
    await callback.answer()

    await safe_edit_message(
        bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text="❌ Создание категории отменено.",
        reply_markup=templates_menu_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=TemplateStateManager.templates_menu,
    )


@router.callback_query(
    CategoryStateManager.confirm_category_creation,
    F.data == "confirm_add_category",
)
async def confirm_category_creation_handler(
    callback: types.CallbackQuery,
    state: FSMContext,
    bot: Bot,
) -> None:
    """Обработчик подтверждения создания категории"""
    await callback.answer()

    data = await state.get_data()
    category_name = data.get("category_name")

    try:
        usecase: CreateCategoryUseCase = container.resolve(CreateCategoryUseCase)
        category = await usecase.execute(dto=CreateCategoryDTO(name=category_name))
        text = (
            f"✅ Категория <b>{category.name}</b> успешно создана.\n"
            "Теперь вы можете создавать шаблоны в этой категории."
        )
    except CategoryAlreadyExists as e:
        text = e.get_user_message()
    except Exception as e:
        logger.error("Ошибка при создании категории: %s", e, exc_info=True)
        text = "❌ Произошла ошибка при создании категории."

    await safe_edit_message(
        bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=templates_menu_ikb(),
    )

    await log_and_set_state(
        message=callback.message,
        state=state,
        new_state=TemplateStateManager.templates_menu,
    )


def validate_category_name(category_name: str) -> bool:
    """Валидирует название категории"""
    return 3 <= len(category_name) <= 50
