import logging

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from container import container
from exceptions.category import CategoryNotFoundError
from keyboards.inline.categories import cancel_category_ikb
from keyboards.inline.templates import templates_menu_ikb
from states import CategoryStateManager
from usecases.categories import GetCategoryByIdUseCase
from utils.send_message import safe_edit_message
from utils.state_logger import log_and_set_state

router = Router(name=__name__)
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("edit_category__"))
async def edit_category_handler(callback: CallbackQuery, state: FSMContext) -> None:
    """Обработчик начала редактирования категории"""
    await callback.answer()

    try:
        # Безопасный парсинг ID категории
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

    logger.info(
        "Пользователь '%s' запустил редактирование категории ID=%d",
        callback.from_user.full_name,
        category_id,
    )

    try:
        usecase: GetCategoryByIdUseCase = container.resolve(GetCategoryByIdUseCase)
        category = await usecase.execute(category_id)

        await state.update_data(category_id=category.id, old_name=category.name)
        await log_and_set_state(
            message=callback.message,
            state=state,
            new_state=CategoryStateManager.editing_category_name,
        )

        text = (
            f"<b>Редактирование категории:</b> {category.name}\n\n"
            "Введите новое название для категории:"
        )

    except CategoryNotFoundError as e:
        logger.warning("Категория ID=%d не найдена: %s", category_id, e)
        text = e.get_user_message()

    except Exception:
        logger.exception("Ошибка при редактировании категории ID=%d", category_id)
        text = "⚠️ Произошла ошибка при попытке изменить категорию."

    await safe_edit_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
        text=text,
        reply_markup=cancel_category_ikb(),
    )
